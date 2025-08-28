from __future__ import annotations

import json
import re
from typing import List, Dict

from app.config import settings
from app.utils import sha256, is_allowed, build_query
from app.search import verified_search
from app.extract import fetch_main_text
from app.retrieve import chunk, bm25_rank
import random

# lightweight stopword list for cloze generation
_STOP = {
    "the","a","an","and","or","but","of","to","in","on","for","with","by","as","at","from","that","this","these","those",
    "is","are","was","were","be","been","being","it","its","their","there","which","who","whom","into","than","then","so","such",
    "may","can","could","should","would","might","will","shall","do","does","did","not","no","yes","we","you","they","he","she"
}


def build_context_from_search(claim: str, top_urls: int = 4, chars: int = 1200) -> List[Dict[str, str]]:
    query = build_query(claim, settings.allowed_domains)
    query_urls = verified_search(query, top=top_urls)
    contexts: List[Dict[str, str]] = []
    for item in query_urls:
        page = fetch_main_text(item["url"])
        if not page:
            continue
        text = page["text"][: chars]
        contexts.append({"title": page["title"], "url": page["url"], "snippet": text})
        if len(contexts) >= 6:
            break
    return contexts


def _format_context_blocks(contexts: List[Dict[str, str]]) -> str:
    blocks = []
    for i, c in enumerate(contexts, start=1):
        blocks.append(f"[{i}] {c['title']} — {c['url']}\n{c['snippet']}")
    return "\n\n".join(blocks)


def generate_mcqs_llm(contexts: List[Dict[str, str]], claim: str, n: int, difficulty: str, style: str) -> List[Dict]:
    if not settings.openai_api_key:
        return []
    try:
        from openai import OpenAI

        # Use env-based auth; also ensure proxies via standard envs only
        client = OpenAI()
        # Use env-based auth; also ensure proxies via standard envs only
        client = OpenAI()
        sys_prompt = (
            "Create multiple-choice questions only from supplied context snippets (WHO/CDC/NHS/NIH/health.gov.au/Cochrane).\n"
            "Each correct answer must be explicitly supported by a sentence in context.\n"
            "Return strict JSON; do not invent facts or URLs; use source_url from the context only.\n"
            "If insufficient context, return an empty items array."
        )
        user_prompt = (
            f"CLAIM:\n\"{claim}\"\n\nCONTEXT:\n" + _format_context_blocks(contexts) +
            f"\n\nGenerate {n} items. Difficulty: {difficulty}. Style: {style}. JSON only."
        )

        chat = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        raw = chat.choices[0].message.content
        data = json.loads(raw or "{}")
        items = data.get("items") or []
        return items
    except Exception:
        return []


def generate_mcqs_llm_with_error(contexts: List[Dict[str, str]], claim: str, n: int, difficulty: str, style: str) -> tuple[List[Dict], str | None]:
    if not settings.openai_api_key:
        return [], "OPENAI_API_KEY missing"
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        sys_prompt = (
            "Create multiple-choice questions only from supplied context snippets (WHO/CDC/NHS/NIH/health.gov.au/Cochrane).\n"
            "Each correct answer must be explicitly supported by a sentence in context.\n"
            "Return strict JSON; do not invent facts or URLs; use source_url from the context only.\n"
            "If insufficient context, return an empty items array."
        )
        user_prompt = (
            f"CLAIM:\n\"{claim}\"\n\nCONTEXT:\n" + _format_context_blocks(contexts) +
            f"\n\nGenerate {n} items. Difficulty: {difficulty}. Style: {style}. JSON only."
        )
        print("user_prompt", user_prompt)
        chat = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        print("chat", chat)
        raw = chat.choices[0].message.content
        print("raw", raw)
        data = json.loads(raw or "{}")
        items = data.get("items") or []
        return items, None
    except Exception as e:
        return [], str(e)


def generate_mcqs_cloze(contexts: List[Dict[str, str]], n: int) -> List[Dict]:
    items: List[Dict] = []
    for c in contexts:
        sentences = re.split(r"(?<=[.!?])\s+", c["snippet"])[:20]
        # collect candidate content words from the whole snippet for distractors
        all_words = [re.sub(r"\W+", "", w) for w in c["snippet"].split()]
        content_pool = [w for w in all_words if len(w) > 3 and w.lower() not in _STOP]
        for sentence in sentences:
            if len(items) >= n:
                break
            words = [w for w in sentence.split() if w.strip()]
            if len(words) < 8:
                continue
            # choose a meaningful keyword
            candidates = [re.sub(r"\W+", "", w) for w in words]
            candidates = [w for w in candidates if len(w) > 4 and w.lower() not in _STOP]
            if not candidates:
                continue
            keyword = max(candidates, key=len)
            if not keyword:
                continue
            blanked = re.sub(re.escape(keyword), "____", sentence, count=1)
            # build unique distractors from content pool
            pool = [w for w in content_pool if w.lower() != keyword.lower()]
            random.shuffle(pool)
            distractors: List[str] = []
            for w in pool:
                w_clean = re.sub(r"\W+$", "", w)
                if w_clean and w_clean.lower() not in {keyword.lower(), *(d.lower() for d in distractors)}:
                    distractors.append(w_clean)
                if len(distractors) == 3:
                    break
            fallback = ["Not stated", "Insufficient evidence", "Unrelated"]
            for f in fallback:
                if len(distractors) == 3:
                    break
                if f.lower() != keyword.lower() and f.lower() not in {d.lower() for d in distractors}:
                    distractors.append(f)
            if len(distractors) < 3:
                continue
            options = [keyword] + distractors[:3]
            # ensure uniqueness and shuffle
            opts_lower = set()
            unique_opts: List[str] = []
            for o in options:
                k = o.strip()
                if not k:
                    continue
                l = k.lower()
                if l not in opts_lower:
                    unique_opts.append(k)
                    opts_lower.add(l)
            if len(unique_opts) != 4:
                continue
            random.shuffle(unique_opts)
            correct_index = unique_opts.index(keyword)
            items.append({
                "question": blanked,
                "options": unique_opts,
                "correct_index": correct_index,
                "explanation": sentence.strip(),
                "source_url": c["url"],
            })
        if len(items) >= n:
            break
    return items


def validate_mcqs(items: List[Dict], contexts: List[Dict[str, str]]) -> List[Dict]:
    allowed_urls = {c["url"] for c in contexts if is_allowed(c["url"])}
    valid: List[Dict] = []
    for it in items:
        raw_opts = it.get("options")
        if not isinstance(raw_opts, list):
            continue
        # normalize option labels like "A) foo", "1. bar"
        norm_opts: List[str] = []
        for o in raw_opts:
            if not isinstance(o, str):
                continue
            s = o.strip()
            s = re.sub(r"^[A-Da-d][\)\.:]\s*", "", s)
            s = re.sub(r"^\d+[\)\.:]\s*", "", s)
            norm_opts.append(s)
        if len(norm_opts) != 4:
            continue
        # derive correct_index from provided index or from a letter/text field
        correct_index = it.get("correct_index")
        if not isinstance(correct_index, int):
            ca = it.get("correct_answer")
            if isinstance(ca, str):
                letter_map = {"A": 0, "B": 1, "C": 2, "D": 3}
                ca_u = ca.strip().upper()
                if ca_u in letter_map:
                    correct_index = letter_map[ca_u]
                else:
                    try:
                        correct_index = norm_opts.index(ca.strip())
                    except Exception:
                        correct_index = None
        if correct_index not in [0, 1, 2, 3]:
            continue
        # ensure options unique (case-insensitive)
        lower = [o.strip().lower() for o in norm_opts]
        if len(set(lower)) != 4:
            continue
        su = it.get("source_url")
        if su not in allowed_urls:
            continue
        valid.append({
            "question": (it.get("question") or "").strip(),
            "options": norm_opts,
            "correct_index": int(correct_index),
            "explanation": (it.get("explanation") or "").strip(),
            "source_url": su,
        })
    return valid


