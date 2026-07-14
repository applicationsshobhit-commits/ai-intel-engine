# Decision Log

A running log of choices made and why. Add an entry whenever a real decision is made —
not every code change (that's what commit messages are for).

## 2026-07-13 — Project kickoff
- **Decision**: Personal project to scrape/monitor AI + followed businesses, with a
  reasoning layer (summarize/prioritize + track entities over time) and a responsive
  web UI (mobile via browser, not native app).
- **Why**: Wanted a single place that turns scattered scraping into prioritized, trend-aware
  signal instead of another raw feed.
- **Stack direction**: Start small — SQLite, scheduled jobs, simple web UI. Upgrade pieces
  (Postgres, native app, etc.) only when the simple version hits a real limit.

## 2026-07-14 — Phase 1: ingestion + storage
- **Decision**: Built Phase 1 in pure Python stdlib (`urllib`, `xml.etree`, `sqlite3`, `json`) —
  no `requests`/`feedparser` dependency, so `python3 ingestion/run.py` runs with zero setup.
- **Sources**: OpenAI news RSS (`openai.com/news/rss.xml`, real working feed) and Hacker News
  "AI" search via the public Algolia API (`hn.algolia.com`) — chosen because both are stable
  JSON/XML endpoints, not HTML scraping, so Phase 1 stays low-fragility.
- **Anthropic dropped from Phase 1**: no public RSS feed, and anthropic.com/news is a
  client-rendered Next.js/Sanity page — plain HTTP fetch only returns an empty shell.
  Revisit once a headless-browser scraper (e.g. Playwright) is added; tracked as a
  Phase 1.5 follow-up rather than blocking the first working pipeline.
- **Result**: `raw_items` deduped by `url` (SQLite `UNIQUE` constraint) — running ingestion
  repeatedly only inserts genuinely new items, verified by running twice (1060 new → 0 new).
