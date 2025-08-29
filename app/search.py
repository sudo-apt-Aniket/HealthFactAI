from __future__ import annotations

import time
from typing import Any

import requests

from .cache import TTLCache
from .core.config import settings
from .utils import is_allowed


SEARCH_CACHE = TTLCache(maxsize=256, ttl_seconds=settings.cache_ttl_search_min * 60)


def _bing_search(query: str, top: int) -> list[dict[str, str]]:
    cache_key = ("bing", query, int(top))
    cached = SEARCH_CACHE.get(cache_key)
    if cached is not None:
        return cached

    if not settings.bing_api_key:
        return []

    params = {
        "q": query,
        "count": int(top),
        "responseFilter": "Webpages",
        "safeSearch": "Strict",
        "textDecorations": False,
        "setLang": "en",
    }
    headers = {
        "Ocp-Apim-Subscription-Key": settings.bing_api_key,
        "User-Agent": "HealthFactAI/1.0 (+verified-search)",
    }
    try:
        resp = requests.get(
            "https://api.bing.microsoft.com/v7.0/search",
            params=params,
            headers=headers,
            timeout=settings.request_timeout_seconds,
        )
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
    except Exception:
        return []

    results: list[dict[str, str]] = []
    for item in (data.get("webPages", {}) or {}).get("value", []):
        url = item.get("url") or ""
        title = item.get("name") or ""
        if not url or not is_allowed(url):
            continue
        results.append({"title": title, "url": url})

    SEARCH_CACHE.set(cache_key, results)
    return results


def langsearch_web_search(query: str, top: int) -> list[dict[str, str]]:
    cache_key = ("langsearch", query, int(top))
    cached = SEARCH_CACHE.get(cache_key)
    if cached is not None:
        return cached

    if not settings.langsearch_api_key:
        return []

    url = "https://api.langsearch.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {settings.langsearch_api_key}",
        "Content-Type": "application/json",
        "User-Agent": "HealthFactAI/1.0 (+verified-search)",
    }
    payload = {
        "query": query,
        "freshness": "noLimit",
        "summary": False,
        "count": int(top),
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=settings.request_timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    # The docs indicate a structure with data.webPages.value similar to Bing
    items = (((data or {}).get("data") or {}).get("webPages") or {}).get("value") or []
    results: list[dict[str, str]] = []
    for item in items:
        u = item.get("url") or ""
        t = item.get("name") or ""
        if not u or not is_allowed(u):
            continue
        results.append({"title": t, "url": u})

    SEARCH_CACHE.set(cache_key, results)
    return results


def verified_search(query: str, top: int) -> list[dict[str, str]]:
    # Prefer LangSearch if configured; fallback to Bing
    results = langsearch_web_search(query, top)
    if results:
        return results
    return _bing_search(query, top)


