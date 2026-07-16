# Project Brief

## Goal
Build a personal intelligence feed for AI and the businesses I follow: scrape relevant
data across the internet, store it, reason over it to surface what actually matters, and
interact with it through a simple, mobile-friendly UI.

In plain terms: instead of manually checking a dozen sources, one system watches them,
tells me what's relevant/urgent, and lets me ask it questions or trace how a company or
topic has evolved over time.

## Architecture (summary)
Five stages, data flows left to right:

1. **Sources** — news/blogs, Twitter/X, company sites, research (arXiv/GitHub).
2. **Ingestion** — normalizes every source into one common `Item` format.
3. **Storage** — `raw_items`, `entities` (companies/people/topics tracked), `mentions`
   (links items to entities).
4. **Reasoning** — a fast pass (summarize + score new items) and a slow pass
   (weekly trend detection across an entity's history).
5. **UI** — feed, entity timeline, ad-hoc Q&A chat. Responsive web, no native app.

Full detail in [architecture.md](architecture.md).

## Approach
Building in phases, smallest usable slice first — not all layers at once.

- **Phase 1 — Ingestion + Storage only.** Pick 1-2 easy sources (e.g. RSS feeds),
  get items landing in SQLite reliably. No reasoning, no UI yet — just prove data flows in.
- **Phase 2 — Reasoning (summarize pass).** Add the LLM summarize/score step on top of
  Phase 1 data. Read results via terminal/notebook, not a UI yet.
- **Phase 3 — UI (feed view only).** Simple web page showing the prioritized feed.
  This is the first end-to-end usable version.
- **Phase 4 — Entities + timeline.** Add entity tracking, mentions table, timeline view.
- **Phase 5 — Trend detection + Q&A chat.** The "connect the dots over time" layer,
  plus the chat interface.
- **Phase 6a — Mobile access, same-WiFi.** Reach the UI from a phone with zero extra
  infrastructure, by hitting the Mac's LAN IP directly. Only works while the Mac is on,
  awake, and on the same network as the phone. Cheapest possible first step.
- **Phase 6b — Mobile access, fully remote.** Reach the UI from anywhere (any network,
  Mac asleep/off) via real hosting. Bigger lift: the ingestion/reasoning pipeline depends
  on the local Codex login, so this needs either a data-sync step (Mac → host) or a
  reasoning backend that isn't tied to the local machine.
- **Later** — add remaining sources (Twitter/X, company sites, research).

Rule of thumb: each phase should end with something runnable, not just code written.
Document decisions in [decisions.md](decisions.md) as they're made, and commit at the
end of each meaningful step so the git history mirrors this phase progression.

## Status
✅ Phase 1 done — ingestion (`ingestion/`) + storage (`storage/`) working end to end.
✅ Phase 2 done — reasoning (`reasoning/`) scores new items against tracked entities
(OpenAI, Anthropic) using a local LLM (Ollama/llama3.2) and writes summaries + relevance
scores into `mentions`. Model is swappable via `reasoning/llm.py`.
✅ Phase 3 done — UI (`ui/`) serves a feed view and per-entity timeline at
`http://localhost:8765`, run via `python3 ui/app.py`. Verified responsive on mobile
and dark mode.
✅ Sources diversified — added TechCrunch, The Verge, Ars Technica alongside OpenAI
and Hacker News, so the feed isn't purely AI-lab content.
✅ Job-relevant sources — added targeted Google News queries for Salesforce stock/earnings,
Salesforce vs. competitor moves, and enterprise AI innovation. Tracked entities now:
OpenAI, Anthropic, Google, Microsoft, Meta, Apple, Amazon, Tesla, Salesforce, HubSpot.
Reasoning prompt tuned to lead summaries with competitive/investment/innovation framing.
✅ Reasoning backend swapped from local Ollama/llama3.2 to Codex (`codex exec`, via the
user's existing Codex login) — noticeably better entity discrimination and summary quality,
at the cost of higher per-item latency (variable, ~7-100s+).
✅ UI tightened for density/scanability — single-line clamped summaries, compact cards.
✅ Automated — `scripts/daily_run.sh` runs ingestion + reasoning (20 items) daily at 7am via
a `launchd` user agent (not cron — blocked by macOS TCC restrictions). Logs to `logs/`.
✅ Feed restricted to this week's news only, and the card UI was redesigned (still
considered rough — user flagged it needs more work).
✅ Phase 6a done — UI reachable from a phone on the same WiFi via the Mac's LAN IP
(`http://<mac-local-ip>:8765`, server already binds to `0.0.0.0`). Breaks if the Mac
sleeps, the UI process isn't running, or the LAN IP changes.
🟡 Phase 6b planned, not started — two architectures decided (see decisions.md):
**Option A** (building first): Render (UI) + Turso (DB, replaces local SQLite) + GitHub
Actions (replaces launchd) + Groq API (replaces Codex, which can't run off-Mac). All free
tier. **Option B** (later, user-built): single VPS (e.g. Oracle free VM), closer to the
current architecture, more ops ownership. Next session: user creates Turso + Groq accounts
and shares config (DB URL/token, API key), then Claude wires up the code changes.
Anthropic ingestion still deferred to Phase 1.5 (needs headless-browser scraping).
Also open: Phase 4 (entity timeline depth), clearing the remaining OpenAI backlog, and
another UI design pass since the current one isn't landing for the user.
