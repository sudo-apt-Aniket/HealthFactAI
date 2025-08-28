from __future__ import annotations

from typing import Iterable
import re

from rank_bm25 import BM25Okapi

from .config import settings
import requests


_WORD = re.compile(r"\w+")


def tokenize(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def chunk(text: str, size: int = 1000, overlap: int = 150) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    cur = ""
    for s in sentences:
        if len(cur) + len(s) + 1 <= size:
            cur = (cur + " " + s).strip()
        else:
            if cur:
                chunks.append(cur)
            cur = s
    if cur:
        chunks.append(cur)
    if overlap and len(chunks) > 1:
        out: list[str] = []
        for i, ch in enumerate(chunks):
            if i == 0:
                out.append(ch)
                continue
            prev = chunks[i - 1]
            tail = prev[-overlap:] if len(prev) > overlap else prev
            out.append((tail + " " + ch).strip())
        return out
    return chunks


def bm25_rank(query: str, passages: list[str], k: int) -> list[tuple[float, str]]:
    if not passages:
        return []
    tokenized_passages = [tokenize(p) for p in passages]
    bm25 = BM25Okapi(tokenized_passages)
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(zip(scores, passages), key=lambda x: (x[0], passages.index(x[1])), reverse=True)
    return ranked[:k]


def embed_rerank(query: str, passages: list[str], top_k: int = 5) -> list[tuple[float, str]]:
    # Use LangSearch Semantic Rerank if enabled; otherwise return top_k unchanged
    if settings.use_langsearch_rerank and settings.langsearch_api_key and passages:
        try:
            url = "https://api.langsearch.com/v1/semantic-rerank"
            headers = {
                "Authorization": f"Bearer {settings.langsearch_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "HealthFactAI/1.0 (+verified-search)",
            }
            payload = {
                "query": query,
                "documents": passages,
                "topK": int(top_k),
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=settings.request_timeout_seconds)
            resp.raise_for_status()
            data = resp.json() or {}
            results = data.get("data") or []
            if isinstance(results, dict):
                results = results.get("results") or []
            scored: list[tuple[float, str]] = []
            for item in results:
                score = float(item.get("score", 0.0))
                idx = int(item.get("index", -1))
                if 0 <= idx < len(passages):
                    scored.append((score, passages[idx]))
            if scored:
                scored.sort(key=lambda x: x[0], reverse=True)
                return scored[:top_k]
        except Exception:
            return [(0.0, p) for p in passages[:top_k]]

    return [(0.0, p) for p in passages[:top_k]]


