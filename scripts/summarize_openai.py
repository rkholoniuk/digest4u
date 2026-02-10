"""Summarize items using OpenAI's API."""
from __future__ import annotations

import os
from typing import Any, Optional
from openai import OpenAI
from .utils import clamp, clean_ws

SYSTEM_INSTRUCTIONS = """You are a research analyst writing concise weekly digests.
Write in crisp bullet-friendly English. Avoid fluff.
If the input text is empty or too short, summarize from title + URL context only.
"""

USER_TEMPLATE = """Summarize the item below for a weekly technical digest about agent marketplaces, ERC-8004, reputation scoring, secure agent execution, and trading/data agents.

Return exactly this JSON (no markdown):
{{
  "summary": "2-3 sentences max",
  "why_it_matters": "1-2 sentences",
  "actions": ["0-3 concrete follow-ups, short imperative verbs"]
}}

Item:
Title: {title}
URL: {url}
Kind: {kind}
Published: {published}

Extracted text (may be empty):
{text}
"""

def summarize_item(
    title: str,
    url: str,
    kind: str = "article",
    published: str = "",
    text: str = "",
    model: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it as an env var (or GitHub secret).")

    model = (model or os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
    try:
        max_output_tokens = int(os.getenv("OPENAI_SUMMARY_TOKENS", str(max_output_tokens or 450)))
    except Exception:
        max_output_tokens = max_output_tokens or 450

    client = OpenAI(api_key=api_key)

    prompt = USER_TEMPLATE.format(
        title=clamp(clean_ws(title), 220),
        url=url,
        kind=kind,
        published=published,
        text=clamp(clean_ws(text), 12000),
    )

    # Use Responses API (recommended for new projects)
    resp = client.responses.create(
        model=model,
        instructions=SYSTEM_INSTRUCTIONS,
        input=prompt,
        text={"format": {"type": "json_object"}},
        max_output_tokens=max_output_tokens,
    )

    # Python SDK convenience: aggregated output text (JSON string here)
    raw = getattr(resp, "output_text", None) or ""
    raw = raw.strip()
    if not raw:
        # Fallback: best-effort in case SDK changes
        raw = str(resp)

    import json
    data = json.loads(raw)
    data["summary"] = clean_ws(data.get("summary",""))
    data["why_it_matters"] = clean_ws(data.get("why_it_matters",""))
    actions = data.get("actions", [])
    if not isinstance(actions, list):
        actions = []
    data["actions"] = [clean_ws(str(a)) for a in actions][:3]
    return data
