"""
Docstring for scripts.analyze
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any
from .utils import clean_ws

THEMES: dict[str, list[str]] = {
    "erc8004": ["erc-8004", "8004", "registry", "reputation", "identity nft", "validation"],
    "payments": ["x402", "payment", "micropayment", "stablecoin", "402"],
    "security": ["tee", "enclave", "attestation", "hsm", "signing", "key"],
    "skills": ["skill", "mcp", "tool", "openclaw", "integration", "agent card"],
    "market": ["marketplace", "directory", "indexer", "rank", "score", "discover"],
    "trading": ["orderbook", "funding", "perp", "options", "iv", "skew", "vrp", "alpha"],
}

def bucket_item(title: str, url: str) -> str:
    """Assign an item to a bucket based on its title and url."""
    text = (clean_ws(title) + " " + (url or "")).lower()
    best = "other"
    best_hits = 0
    for theme, words in THEMES.items():
        hits = sum(1 for w in words if w in text)
        if hits > best_hits:
            best, best_hits = theme, hits
    return best

def score_item(kind: str, bucket: str, title: str) -> float:
    """Assign a score to an item based on its kind, bucket, and title."""
    base = 1.0
    if kind == "release":
        base += 1.5
    elif kind == "commit":
        base += 1.0
    if bucket != "other":
        base += 1.0
    if "erc-8004" in (title or "").lower():
        base += 0.5
    return base

def analyze(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze items and assign them to buckets with scores."""
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for it in items:
        b = bucket_item(it.get("title",""), it.get("url",""))
        it["bucket"] = b
        it["score"] = score_item(it.get("kind",""), b, it.get("title",""))
        buckets[b].append(it)

    for b in buckets:
        buckets[b].sort(key=lambda x: (x.get("score",0), x.get("published","")), reverse=True)

    return {"buckets": buckets, "items": items}
