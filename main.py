from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
import sqlite3

from database import get_db
from auth import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from pydantic import BaseModel, Field
from typing import List, Optional
from app.config import settings
from app.utils import build_query, sha256
from app.search import verified_search
from app.extract import fetch_main_text
from app.retrieve import chunk, bm25_rank, embed_rerank
from app.quiz.schemas import QuizFromClaimRequest, QuizFromClaimResponse, QuizItem, GradeQuizRequest, GradeQuizResponse
from app.quiz.service import build_context_from_search, generate_mcqs_llm_with_error, validate_mcqs
from app.quiz.grader import grade

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ✅ Register new user
@app.post("/register/")
def register(username: str, password: str):
    conn = get_db()
    c = conn.cursor()
    try:
        hashed_pw = get_password_hash(password)
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        return {"msg": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()

# ✅ Login → return JWT
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users WHERE username=?", (form_data.username,))
    user = c.fetchone()
    conn.close()

    if not user or not verify_password(form_data.password, user[2]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user[1]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ✅ Protected route
@app.get("/me")
def read_users_me(token: str = Depends(oauth2_scheme)):
    from jose import jwt, JWTError
    from auth import SECRET_KEY, ALGORITHM

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")


class SearchRequest(BaseModel):
    claim: str
    top_urls: int = Field(default=6, ge=1, le=10)
    passages_per_url: int = Field(default=3, ge=1, le=5)
    use_embed_rerank: Optional[bool] = None


class SourceOut(BaseModel):
    title: str
    url: str
    passages: List[str]


class MetaOut(BaseModel):
    claim_hash: Optional[str] = None
    searched_domains: Optional[List[str]] = None
    counts: Optional[dict] = None
    timings_ms: Optional[dict] = None
    reason: Optional[str] = None


class SearchResponse(BaseModel):
    status: str
    sources: List[SourceOut]
    meta: MetaOut


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/search_verified", response_model=SearchResponse)
def search_verified(payload: SearchRequest):
    claim = (payload.claim or "").strip()
    if not claim:
        raise HTTPException(status_code=400, detail="Empty claim")

    claim_hash = sha256(claim)

    # Build query limited to allowlist domains
    query = build_query(claim, settings.allowed_domains)

    urls = verified_search(query, top=payload.top_urls)

    if not urls:
        return {
            "status": "ok",
            "sources": [],
            "meta": {
                "reason": "No allowlisted results",
                "claim_hash": claim_hash,
            },
        }

    sources = []
    total_passages = 0
    fetched = 0
    extracted = 0
    for item in urls:
        page = fetch_main_text(item["url"])
        fetched += 1
        if not page:
            continue
        extracted += 1
        pieces = chunk(page["text"], size=1000, overlap=150)
        ranked = bm25_rank(claim, pieces, k=payload.passages_per_url)
        passages = [p for _, p in ranked]
        total_passages += len(passages)
        if passages:
            sources.append({
                "title": page["title"],
                "url": page["url"],
                "passages": passages,
            })

    # Optional rerank across all passages
    use_rerank = payload.use_embed_rerank if payload.use_embed_rerank is not None else settings.use_embed_rerank
    if use_rerank and sources:
        flat_passages = []
        for s in sources:
            for p in s["passages"]:
                flat_passages.append((s["url"], p, s["title"]))
        reranked = embed_rerank(claim, [p for _, p, _ in flat_passages], top_k=min(12, len(flat_passages)))
        # regroup by url keeping top selections
        selected = set(p for _, p in reranked)
        new_sources = []
        for s in sources:
            new_passages = [p for p in s["passages"] if p in selected]
            if new_passages:
                new_sources.append({"title": s["title"], "url": s["url"], "passages": new_passages})
        sources = new_sources

    if not sources:
        return {
            "status": "ok",
            "sources": [],
            "meta": {
                "reason": "No allowlisted results or failed extraction.",
                "claim_hash": claim_hash,
            },
        }

    return {
        "status": "ok",
        "sources": sources,
        "meta": {
            "claim_hash": claim_hash,
            "searched_domains": settings.allowed_domains,
            "counts": {
                "urls": len(sources),
                "passages": sum(len(s["passages"]) for s in sources),
                "fetched": fetched,
                "extracted": extracted
            },
        },
    }


@app.post("/quiz_from_claim", response_model=QuizFromClaimResponse)
def quiz_from_claim(payload: QuizFromClaimRequest):
    claim = (payload.claim or "").strip()
    if not claim:
        raise HTTPException(status_code=400, detail="Empty claim")
    claim_hash = sha256(claim)

    contexts = build_context_from_search(claim, top_urls=4, chars=1200)
    if not contexts:
        return {"status": "ok", "items": [], "meta": {"reason": "Insufficient context from allow-listed sources.", "claim_hash": claim_hash}}

    items, llm_err = generate_mcqs_llm_with_error(contexts, claim, payload.num_questions, payload.difficulty, payload.style)
    print("items", items)
    validated = validate_mcqs(items, contexts)
    print("validated", validated)
    print("len(contexts)", len(contexts))
    if not validated:
        return {"status": "ok", "items": [], "meta": {"reason": "LLM returned no valid items after validation.", "claim_hash": claim_hash, "sources_used": len(contexts), "llm_error": llm_err}}

    # Cap to requested number
    validated = validated[: payload.num_questions]
    return {"status": "ok", "items": validated, "meta": {"claim_hash": claim_hash, "sources_used": len(contexts)}}


@app.post("/grade_quiz", response_model=GradeQuizResponse)
def grade_quiz(payload: GradeQuizRequest):
    result = grade(payload.answers, payload.key)
    return result
