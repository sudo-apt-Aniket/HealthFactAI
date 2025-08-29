from __future__ import annotations

import hashlib
import time
from contextlib import contextmanager
from urllib.parse import urlparse

from .core.config import settings


def is_allowed(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    # Match exact domain or subdomain of allowlist entries
    for allowed in settings.allowed_domains:
        if host == allowed or host.endswith("." + allowed):
            return True
    return False


def build_query(claim: str, allowlist: list[str]) -> str:
    sites = " OR ".join([f"site:{d}" for d in allowlist])
    return f"{claim} ({sites})"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@contextmanager
def timed() -> tuple[None, dict[str, int]]:
    start = time.time()
    timings: dict[str, int] = {}
    try:
        yield timings
    finally:
        timings["total"] = int((time.time() - start) * 1000)


