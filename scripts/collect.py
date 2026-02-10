"""
Collect items from various sources like RSS feeds and GitHub repositories.
"""
from __future__ import annotations

import os
import requests
import feedparser
from typing import Any
from .utils import sha256, clean_ws

def collect_rss(url: str) -> list[dict[str, Any]]:
    """
    collect_rss fetches and parses an RSS feed, returning a list of items with their metadata.
    
    :param url: Description
    :type url: str
    :return: Description
    :rtype: list[dict[str, Any]]
    """
    feed = feedparser.parse(url)
    items: list[dict[str, Any]] = []
    for e in getattr(feed, "entries", []) or []:
        link = getattr(e, "link", None)
        if not link:
            continue
        title = clean_ws(getattr(e, "title", "") or "")
        published = getattr(e, "published", "") or getattr(e, "updated", "") or ""
        items.append({
            "id": sha256(link),
            "source": url,
            "title": title,
            "url": link,
            "published": published,
            "kind": "article",
        })
    return items

def _gh_headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def github_releases(repo: str) -> list[dict[str, Any]]:
    """
    check_github_releases fetches the latest releases from a GitHub repository and returns them as a list of items with their metadata.
    
    :param repo: Description
    :type repo: str
    :return: Description
    :rtype: list[dict[str, Any]]
    """
    r = requests.get(f"https://api.github.com/repos/{repo}/releases", headers=_gh_headers(), timeout=30)
    r.raise_for_status()
    out: list[dict[str, Any]] = []
    for rel in r.json()[:30]:
        url = rel.get("html_url")
        if not url:
            continue
        out.append({
            "id": sha256(url),
            "source": f"github:{repo}:releases",
            "title": clean_ws(rel.get("name") or rel.get("tag_name") or "release"),
            "url": url,
            "published": rel.get("published_at") or "",
            "kind": "release",
        })
    return out

def github_commits(repo: str, branch: str = "main") -> list[dict[str, Any]]:
    """
    github_commits fetches the latest commits from a GitHub repository and returns them as a list of items with their metadata.
    
    :param repo: Description
    :type repo: str
    :param branch: Description
    :type branch: str
    :return: Description
    :rtype: list[dict[str, Any]]
    """
    r = requests.get(
        f"https://api.github.com/repos/{repo}/commits",
        params={"sha": branch, "per_page": 30},
        headers=_gh_headers(),
        timeout=30,
    )
    r.raise_for_status()
    out: list[dict[str, Any]] = []
    for c in r.json():
        url = c.get("html_url")
        if not url:
            continue
        msg = (c.get("commit", {}).get("message") or "").split("\n")[0]
        out.append({
            "id": sha256(url),
            "source": f"github:{repo}:commits",
            "title": clean_ws(msg)[:180],
            "url": url,
            "published": c.get("commit", {}).get("author", {}).get("date") or "",
            "kind": "commit",
        })
    return out

def collect_all(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """
    collect_all iterates over the configured sources (RSS feeds, GitHub releases, GitHub commits) and collects items from all of them, returning a combined list of items with their metadata.
    :param cfg: Description
    :type cfg: dict[str, Any]
    :return: Description
    :rtype: list[dict[str, Any]]
    """

    out: list[dict[str, Any]] = []
    for s in cfg.get("rss", []) or []:
        t = s.get("type")
        if t == "rss":
            out.extend(collect_rss(s["url"]))
        elif t == "github_releases":
            out.extend(github_releases(s["repo"]))
        elif t == "github_commits":
            out.extend(github_commits(s["repo"], s.get("branch", "main")))
    return out
