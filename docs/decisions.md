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

## 2026-07-14 — Phase 2: reasoning (summarize + score)
- **Decision**: Use a local LLM (Ollama, `llama3.2` 3B) instead of the Anthropic API for the
  scoring pass.
- **Why**: Anthropic API is pay-as-you-go with no persistent free tier; wanted to build and
  iterate on the pipeline without a running cost while the prompt/approach is still unstable.
  Ollama + llama3.2 run fully local and free, ~1s/item.
- **Trade-off accepted**: llama3.2 is noisy — under-matches some clearly-relevant items and
  occasionally over-matches. Fine for proving the pipeline shape; `reasoning/llm.py` isolates
  the model call behind one function (`call_llm`), so swapping in Claude or a bigger model
  later is a one-file change, not a rewrite.
- **Schema change**: added `raw_items.reasoned_at` to track which items have been scored
  (rather than inferring from `mentions` existing, which breaks for zero-match items).
- **Result**: full loop verified — raw item → LLM scoring → `mentions` row with entity,
  relevance_score, and a real generated summary. Tested on 18 items, no crashes after
  hardening the JSON parsing against malformed model output.
