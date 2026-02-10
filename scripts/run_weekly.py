"""Main script to run the weekly digest process: collect, analyze, enrich, and build the digest."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

import yaml

if __package__ in (None, ""):
    import sys

    # Allow running as `python scripts/run_weekly.py` by fixing sys.path/package.
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    __package__ = "scripts"

from .db import connect, upsert_item, get_item
from .collect import collect_all
from .analyze import analyze
from .fetch_text import fetch_article_text
from .summarize_openai import summarize_item
from .build_digest import build_digest
from .utils import now_iso, sha256

STATE_PATH = Path("data/state.json")

def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"seen": {}, "last_run": None}

def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")

def main():
    cfg = yaml.safe_load(Path("sources.yaml").read_text(encoding="utf-8"))
    state = load_state()
    seen = state.setdefault("seen", {})

    conn = connect()

    raw_items = collect_all(cfg)

    new_items: list[dict[str, Any]] = []
    for it in raw_items:
        iid = it["id"]
        if iid in seen:
            continue
        seen[iid] = {"url": it["url"], "first_seen": now_iso()}
        it["fetched_at"] = now_iso()
        new_items.append(it)

    if not new_items:
        print("No new items found.")
        state["last_run"] = now_iso()
        save_state(state)
        return

    analysis = analyze(new_items)

    # Enrich: fetch text + summarize (cached in sqlite)
    for it in analysis["items"]:
        existing = get_item(conn, it["id"])
        if existing and existing.get("summary"):
            # already summarized/cached
            it.update({
                "summary": existing.get("summary"),
                "why_it_matters": existing.get("why_it_matters"),
                "actions": json.loads(existing.get("actions") or "[]") if isinstance(existing.get("actions"), str) else (existing.get("actions") or []),
            })
            continue

        # Try to fetch article text (best effort)
        text, content_hash = ("", "")
        if it.get("kind") == "article":
            text, content_hash = fetch_article_text(it["url"])
        it["content_text"] = text
        it["content_hash"] = content_hash

        # Summarize with OpenAI (required)
        data = summarize_item(
            title=it.get("title",""),
            url=it.get("url",""),
            kind=it.get("kind","article"),
            published=it.get("published",""),
            text=text,
        )
        it["summary"] = data.get("summary","")
        it["why_it_matters"] = data.get("why_it_matters","")
        it["actions"] = data.get("actions", [])

        # Persist
        db_row = dict(it)
        db_row["actions"] = json.dumps(it.get("actions") or [])
        upsert_item(conn, db_row)

    # Build digest
    digest_path = build_digest(analysis["items"], analysis["buckets"])

    state["last_run"] = now_iso()
    save_state(state)
    print(f"Digest updated: {digest_path.as_posix()}")

if __name__ == "__main__":
    main()
