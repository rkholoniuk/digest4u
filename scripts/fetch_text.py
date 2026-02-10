"""Fetch and extract text content from URLs."""
from __future__ import annotations

import requests
import trafilatura
from .utils import clean_ws, sha256

def fetch_article_text(url: str, timeout: int = 30) -> tuple[str, str]:
    """Return (text, content_hash). Empty text if extraction fails."""
    try:
        r = requests.get(url, timeout=timeout, headers={
            "User-Agent": "agent-digest/1.0 (+https://github.com)"
        })
        r.raise_for_status()
        downloaded = trafilatura.extract(r.text, include_comments=False, include_tables=False)
        text = clean_ws(downloaded or "")
        if not text:
            return "", ""
        return text, sha256(text[:20000])  # hash first chunk for stability
    except Exception:
        return "", ""
