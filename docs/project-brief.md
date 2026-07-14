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
- **Later** — add remaining sources (Twitter/X, company sites, research), harden hosting.

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
and Hacker News, so the feed isn't purely AI-lab content. Tracked entities expanded
to OpenAI, Anthropic, Google, Microsoft, Meta, Apple, Amazon, Tesla.
Anthropic ingestion still deferred to Phase 1.5 (needs headless-browser scraping).
Next: Phase 4, entities + timeline depth, or scoring the remaining backlog.
