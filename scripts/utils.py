"""Utility functions for hashing, date formatting, string cleaning, and safe integer conversion."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Optional

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def clean_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def clamp(s: str, n: int) -> str:
    s = s or ""
    return s if len(s) <= n else s[: n - 1] + "…"

def safe_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default
