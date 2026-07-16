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

## 2026-07-14 — Phase 3: UI (feed + entity timeline)
- **Decision**: Built with Python's stdlib `http.server` instead of Flask/FastAPI — keeps
  the zero-install approach consistent with the rest of the project. Two views: `/` (feed,
  all mentions sorted by relevance then recency) and `/entity?name=X` (timeline for one
  entity). No JS framework; server-rendered HTML with a small responsive CSS block.
- **Bug found via manual testing**: llama3.2 was emitting mentions with relevance_score as
  low as 0.0–0.2 instead of omitting irrelevant entities as the prompt instructed (e.g.
  OpenAI-only articles showing up under "Anthropic" at 0.0 relevance). Fixed with a
  `MIN_RELEVANCE = 0.5` filter in `ui/queries.py` rather than re-tuning the prompt again —
  cheaper fix, and a query-layer threshold is generally useful regardless of model quality.
- **Verified**: checked in-browser at both desktop and mobile viewport widths; feed renders
  correctly, entity filter correctly returns empty (not garbage) for Anthropic since we
  don't ingest Anthropic content yet (Phase 1.5).

## 2026-07-14 — Diversify sources + UI redesign
- **Why**: feed was 100% AI-lab content (OpenAI + AI-tagged HN posts) which doesn't match the
  original goal of tracking "AI and the businesses I follow" broadly.
- **New sources**: TechCrunch and Ars Technica (RSS 2.0) and The Verge (Atom — different feed
  format, required `ingestion/sources/rss.py` to handle both `<item>` and `<entry>` shapes).
  Refactored source registration in `ingestion/run.py` from one-file-per-source to
  `(name, fetch_fn)` tuples using `functools.partial`, since RSS sources now differ only by
  URL, not by parsing logic.
- **Expanded tracked entities**: OpenAI, Anthropic, Google, Microsoft, Meta, Apple, Amazon,
  Tesla — so the reasoning pass has real non-AI-lab companies to match against.
- **Bug found**: `get_unscored_items` processed oldest-inserted items first (SQLite default
  rowid order), so the huge original OpenAI backlog kept crowding out newer, more diverse
  items in every reasoning batch. Fixed by ordering `ORDER BY fetched_at DESC` — also just a
  better default going forward (freshest items reasoned first).
- **UI redesign**: rebuilt `ui/app.py` — pill-style nav with active state, per-entity color
  tags (borrowed from the CDS palette), relevance shown as a percentage, light/dark mode via
  `prefers-color-scheme`. Verified in-browser: desktop light, desktop dark, and mobile.
- **Known noise**: local model still produces occasional false-positive entity matches (e.g.
  an OpenAI-only article tagged 80% relevant to Tesla) — same accepted trade-off as Phase 2,
  not a new issue.

## 2026-07-14 — Job-relevant sources (Salesforce/CRM/investment) + succinct UI
- **Why**: reader works in the Salesforce/enterprise-CRM ecosystem; wanted the feed to surface
  competitive moves, investment/stock signal, and innovation — not just generic AI news.
- **New sources**: `ingestion/sources/google_news.py` — a Google News RSS *search* source
  (`news.google.com/rss/search?q=...`), used for three targeted queries: Salesforce
  stock/earnings/investment, Salesforce vs. Microsoft Dynamics/HubSpot competition, and AI
  innovation in enterprise software. Chosen over the official Salesforce blog because it
  captures third-party/analyst coverage (investment angle), which a company's own blog won't.
- **Tracked entities**: added Salesforce, HubSpot.
- **Prompt change**: `reasoning/score.py` now explicitly frames the reader as working in
  enterprise software/CRM and asks summaries to lead with *why it matters*
  (competitive threat / investment signal / innovation) instead of restating the headline,
  capped at 15 words.
- **UI**: tightened `ui/app.py` for density — title + entity tag on one line, single-line
  clamped summary, smaller nav pills/fonts. Goal was scanability, not exhaustive detail per card.
- **Ops note**: launching multiple overlapping background reasoning batches accidentally
  starved Ollama (3 concurrent processes made a trivial call take 14s instead of ~1s) —
  lesson: always confirm a prior background reasoning run has actually finished
  (`ps aux | grep reasoning/run.py`) before starting another.

## 2026-07-14 — Swap reasoning backend: Ollama → Codex
- **Decision**: `reasoning/llm.py` now shells out to `codex exec` (the CLI bundled inside the
  Codex.app desktop app at `/Applications/Codex.app/Contents/Resources/codex`) instead of
  calling local Ollama. Uses the user's existing Codex login — no new API key or billing setup.
- **Why**: side-by-side test showed materially better output — correct multi-entity
  discrimination (e.g. one item correctly scored Salesforce 1.0 primary, Microsoft 0.75 and
  OpenAI 0.7 as competitive context) versus llama3.2's frequent false positives/negatives.
- **Trade-off**: `codex exec` spins up a full agentic CLI session per call (system prompt,
  tools, sandbox), not a lightweight completion endpoint. Per-item latency was highly variable
  in practice — some calls returned in ~7s, one hung well past the 120s subprocess timeout and
  had to be killed manually. Not suited to large unattended batches yet; fine for the smaller,
  higher-value batches (like the 37-item Salesforce backlog) run so far.
- **Implementation**: writes the model's final answer to a temp file via `codex exec -o` rather
  than parsing stdout text, since stdout also contains session/log noise.
- **Result**: cleared the Salesforce-focused Google News backlog (53 total Salesforce mentions
  after this run), with summaries that read as real investment/competitive signal — analyst
  price targets, institutional stock holdings, competitor moves.

## 2026-07-16 — Automate ingestion + reasoning (launchd)
- **Decision**: added `scripts/daily_run.sh` (runs `ingestion/run.py` then
  `reasoning/run.py --limit 20`, logs to `logs/`, keeps the last 30 log files) and scheduled
  it daily at 7am via a `launchd` user agent
  (`~/Library/LaunchAgents/com.aiintelengine.dailyrun.plist`).
- **Why launchd, not cron**: `crontab -e` failed with `Operation not permitted` — macOS blocks
  cron under TCC/Full Disk Access restrictions for sandboxed processes. `launchd` is the native
  macOS scheduler and isn't subject to that restriction.
- **Why limit 20/run**: Codex reasoning is slow and variable (~10-75s/item observed, one call
  hung entirely). Capping each automated run at 20 items keeps it roughly bounded rather than
  risking a run that never finishes; the backlog clears gradually over several days.
- **Bug fixed while building this**: `reasoning/llm.py`'s `subprocess.run(timeout=120)` only
  killed the direct `codex exec` child — `codex` spawns its own child processes, which survived
  as orphans after a timeout (this is what caused the 22-minute hang seen earlier). Switched to
  `subprocess.Popen(start_new_session=True)` + `os.killpg(...)` on timeout so the whole process
  group gets killed. Necessary before trusting this to run unattended.
- **Verified**: `launchctl load` registered the job; `launchctl start` manually triggered it,
  confirmed via a fresh log file and a live `reasoning/run.py` process actually calling Codex.

## 2026-07-16 — Restrict to this week's news, redesign UI
- **Decision**: added `ingestion/item.is_this_week()` — parses both RFC822 (RSS `pubDate`) and
  ISO 8601 (Atom/HN) date formats, keeps items with no parseable date rather than dropping them
  silently. Applied at fetch time in `ingestion/run.py` (skip old items before insert) and again
  in `ui/queries.py` (filter what's displayed), since the existing DB already had older backlog
  items from before this filter existed — filtering only new fetches wouldn't have hidden those.
  Google News queries' own `when:` window bumped from 3d to 7d to match.
- **Verified**: OpenAI's RSS fetch dropped from 40 items/run to 8 "this week" after the filter;
  feed now shows only July 2026 dates instead of mixing in 2016-era items.
- **UI redesign**: reworked `ui/app.py` visual style — colored left-border accent per entity,
  a small relevance bar (not just a percentage), warmer neutral palette, tighter type scale,
  subtle card shadow. Verified in-browser at light and dark mode.
- **Note**: user says the UI still isn't landing visually despite this pass — flagged as a
  known open item, not resolved. Another design iteration is expected later.

## 2026-07-16 — Mobile access, split into two phases
- **Decision**: split "host it for mobile" into Phase 6a (same-WiFi, LAN IP, no new
  infrastructure) and Phase 6b (fully remote, any network, Mac can be off). Doing 6a first
  since it's nearly free — `ui/app.py` already binds to `0.0.0.0`, so the only missing piece
  was finding the Mac's LAN IP (`ipconfig getifaddr en0` → `192.168.1.126`) and confirming the
  server actually answers on that address, not just `localhost`.
- **Why split**: Phase 6b is a real jump in complexity — the reasoning pipeline depends on the
  local Codex CLI login, so remote hosting needs either a data-sync step (Mac → host) or a
  reasoning backend not tied to this machine. Not worth blocking mobile access on solving that
  now when 6a covers "check the feed from my phone at home" today.
- **Known limitations of 6a**: only works while the Mac is awake, `ui/app.py` is running, and
  the phone is on the same WiFi; the LAN IP can change if the router reassigns it (DHCP).
- **Decision**: kept the UI server manual (`python3 ui/app.py`, not auto-started via launchd)
  per user preference — user wants to start it themselves when needed rather than have it
  always running in the background.
