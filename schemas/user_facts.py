import json
import sqlite3
from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from database import get_db
from auth import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError

from schemas.user_facts import FactCreate, FactResponse, UserFactsListResponse, UserStatsResponse
from services.streak_service import compute_new_streak


router = APIRouter(prefix="/user", tags=["user_facts"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def _token_username(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")


def _fetch_user_by_id(conn: sqlite3.Connection, user_id: int):
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    return {"id": row[0], "username": row[1]} if row else None


def _ensure_user_access(conn: sqlite3.Connection, user_id: int, username_from_token: str):
    user = _fetch_user_by_id(conn, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["username"] != username_from_token:
        raise HTTPException(status_code=403, detail="Forbidden: cannot access other user's data")
    return user


def _load_facts(raw: Optional[str]):
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_facts(conn: sqlite3.Connection, user_id: int, facts):
    c = conn.cursor()
    c.execute("UPDATE users SET facts_learned = ? WHERE id = ?", (json.dumps(facts, separators=(",", ":")), user_id))


@router.post("/{user_id}/facts", response_model=FactResponse)
def add_fact(user_id: int, payload: FactCreate, token_username: str = Depends(_token_username)):
    conn = get_db()
    try:
        _ensure_user_access(conn, user_id, token_username)

        c = conn.cursor()
        c.execute("SELECT facts_learned, total_facts_count, current_streak, longest_streak, last_activity_date FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        facts = _load_facts(row[0])
        now = datetime.utcnow()
        new_item = {
            "content": payload.content,
            "category": payload.category,
            "source_url": payload.source_url,
            "learned_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        facts.append(new_item)

        _save_facts(conn, user_id, facts)

        total = (row[1] or 0) + 1
        new_current, new_longest, new_last_activity = compute_new_streak(row[2], row[3], row[4])
        c.execute(
            "UPDATE users SET total_facts_count = ?, current_streak = ?, longest_streak = ?, last_activity_date = ? WHERE id = ?",
            (total, new_current, new_longest, new_last_activity, user_id),
        )

        conn.commit()
        return FactResponse(
            content=new_item["content"],
            category=new_item["category"],
            source_url=new_item["source_url"],
            learned_at=now,
        )
    except sqlite3.Error:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        conn.close()


@router.get("/{user_id}/facts", response_model=UserFactsListResponse)
def get_facts(user_id: int, limit: int = 50, category: Optional[str] = None, token_username: str = Depends(_token_username)):
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
    conn = get_db()
    try:
        _ensure_user_access(conn, user_id, token_username)
        c = conn.cursor()
        c.execute("SELECT facts_learned FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        facts = _load_facts(row[0])
        if category:
            facts = [f for f in facts if f.get("category") == category]

        def _parse_dt(s: Optional[str]):
            if not s:
                return datetime.min
            try:
                return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                return datetime.min

        facts.sort(key=lambda f: _parse_dt(f.get("learned_at")), reverse=True)
        items = facts[:limit]
        result_items = [
            FactResponse(
                content=i.get("content", ""),
                category=i.get("category"),
                source_url=i.get("source_url"),
                learned_at=_parse_dt(i.get("learned_at")),
            )
            for i in items
        ]
        return UserFactsListResponse(items=result_items, total=len(facts))
    finally:
        conn.close()


@router.get("/{user_id}/streaks", response_model=UserStatsResponse)
def get_streaks(user_id: int, token_username: str = Depends(_token_username)):
    conn = get_db()
    try:
        _ensure_user_access(conn, user_id, token_username)
        c = conn.cursor()
        c.execute(
            "SELECT current_streak, longest_streak, total_facts_count, facts_learned, last_activity_date FROM users WHERE id = ?",
            (user_id,),
        )
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        current_streak = row[0] or 0
        longest_streak = row[1] or 0
        total_facts_count = row[2] or 0
        facts = _load_facts(row[3])
        last_activity_date = row[4]

        today = date.today()
        week_ago = today - timedelta(days=6)
        facts_this_week = 0
        for f in facts:
            s = f.get("learned_at")
            if not s:
                continue
            try:
                d = datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").date()
            except Exception:
                continue
            if week_ago <= d <= today:
                facts_this_week += 1

        return UserStatsResponse(
            current_streak=current_streak,
            longest_streak=longest_streak,
            total_facts_count=total_facts_count,
            facts_this_week=facts_this_week,
            last_activity_date=last_activity_date,
        )
    finally:
        conn.close()


