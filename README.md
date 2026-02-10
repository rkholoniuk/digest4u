# Agent Weekly Digest (LLM Summaries)

A small, production-friendly pipeline that:
1) collects new items from RSS/Atom + GitHub (releases/commits),
2) deduplicates + stores state in SQLite,
3) optionally fetches article text,
4) summarizes with OpenAI (Responses API),
5) generates a weekly Markdown digest,
6) commits updates automatically via GitHub Actions.

## Quick start (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set OpenAI key (required for summaries)
export OPENAI_API_KEY="sk-...."
export OPENAI_MODEL="gpt-4o-mini"

python scripts/run_weekly.py
```

Digest output: `digest/<YEAR>/<YEAR>-W<WW>.md`

## GitHub Actions setup

Add these repo secrets:
- `OPENAI_API_KEY` (required)
- `GITHUB_TOKEN` is provided automatically by GitHub Actions

Then run:
- Actions → "Weekly Digest" → Run workflow
or wait for the Monday schedule.

## Configuration

Edit `sources.yaml` to add RSS feeds and GitHub repos to track.

## Notes

- This project uses the OpenAI API key.
- Summaries are cached in SQLite; you only pay once per URL.
