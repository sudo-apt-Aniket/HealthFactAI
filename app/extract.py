from __future__ import annotations

from typing import Any

import requests
from bs4 import BeautifulSoup

from .cache import TTLCache
from .config import settings
from .utils import is_allowed


PAGE_CACHE = TTLCache(maxsize=256, ttl_seconds=settings.cache_ttl_page_min * 60)


def fetch_main_text(url: str) -> dict[str, str] | None:
    if not is_allowed(url):
        return None

    cached = PAGE_CACHE.get(url)
    if cached is not None:
        return cached

    headers = {"User-Agent": "HealthFactAI/1.0 (+verified-search)"}
    try:
        resp = requests.get(url, headers=headers, timeout=settings.request_timeout_seconds)
        resp.raise_for_status()
        html = resp.text
    except Exception:
        return None

    # Try readability first, but import lazily to avoid hard dependency at startup
    try:
        from readability import Document  # type: ignore

        doc = Document(html)
        title = doc.short_title() or ""
        summary_html = doc.summary(html_partial=True)
        soup = BeautifulSoup(summary_html, "lxml")
        text = soup.get_text(" ", strip=True)
    except Exception:
        # fallback: raw soup
        soup = BeautifulSoup(html, "lxml")
        title = (soup.title.string if soup.title else "") or ""
        text = soup.get_text(" ", strip=True)

    if not text or len(text) < 400:
        return None

    result = {"title": title, "url": url, "text": text}
    PAGE_CACHE.set(url, result)
    return result


