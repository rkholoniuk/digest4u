"""
Build a weekly digest markdown file from analyzed items.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Iterable

def iso_week_path(now: datetime | None = None) -> Path:
    """Return a Path for the current ISO week, e.g. digest/2024/2024-W24.md"""
    now = now or datetime.now(timezone.utc)
    year, week, _ = now.isocalendar()
    return Path(f"digest/{year}/{year}-W{week:02d}.md")

def md_escape(s: str) -> str:
    """Escape markdown special characters in a string."""
    return (s or "").replace("\n", " ").strip()

def build_digest(items: list[dict[str, Any]], buckets: dict[str, list[dict[str, Any]]]) -> Path:
    """Build a markdown digest file from items and their assigned buckets."""
    p = iso_week_path()
    p.parent.mkdir(parents=True, exist_ok=True)

    total = len(items)
    included = sum(min(len(v), 8) for v in buckets.values())

    lines: list[str] = []
    lines.append(f"# Weekly Agent Digest — {p.stem}")
    lines.append("")
    lines.append(f"**Scorecard:** New items: {total} | Included: {included} | Clusters: {len(buckets)}")
    lines.append("")

    order = ["erc8004","market","skills","payments","security","trading","other"]
    for theme in order:
        lst = buckets.get(theme) or []
        if not lst:
            continue
        lines.append(f"## {theme.upper()}")
        lines.append("")
        for it in lst[:8]:
            title = md_escape(it.get("title","(untitled)"))
            url = it.get("url","")
            summary = md_escape(it.get("summary",""))
            why = md_escape(it.get("why_it_matters",""))
            actions = it.get("actions") or []
            lines.append(f"### [{title}]({url})")
            if summary:
                lines.append(f"- **Summary:** {summary}")
            if why:
                lines.append(f"- **Why it matters:** {why}")
            if actions:
                lines.append(f"- **Follow-ups:**")
                for a in actions[:3]:
                    lines.append(f"  - {md_escape(str(a))}")
            lines.append("")
        lines.append("")

    p.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    readme = Path("digest/README.md")
    rel = p.relative_to(Path("digest"))
    readme.write_text(f"Latest: [{p.stem}]({rel.as_posix()})\n", encoding="utf-8")
    return p
