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
