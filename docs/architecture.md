# Architecture

See the diagram (rendered as an Artifact in chat, and described below in text so it stays in git).

## Components

1. **Ingestion layer** — scheduled jobs pulling from RSS/blogs, Twitter/X, company sites
   (press/jobs/pricing), and research sources (arXiv, GitHub trending). Each source normalizes
   into a common `Item { source, url, title, content, entities, timestamp }`.

2. **Storage** — SQLite to start (Postgres + pgvector later if needed).
   - `raw_items`: every scraped item
   - `entities`: companies/people/topics being tracked
   - `mentions`: join table linking items to entities, with relevance score

3. **Reasoning layer**
   - Near-real-time pass: embed + dedupe new items, LLM-summarize, score relevance/urgency
     per tracked entity.
   - Periodic pass (e.g. weekly): look across an entity's history to surface trends.

4. **UI** — responsive web app (feed view, entity timeline view, ad-hoc Q&A chat).
   Mobile covered via responsive design rather than a native app.

## Data flow
Sources → Ingestion (normalize) → Storage (raw_items) → Reasoning (summarize/score/link entities)
→ Storage (mentions + summaries) → UI (feed / timeline / chat)

## Open questions / decisions to make
- Twitter/X: official API (rate-limited, paid) vs. scraping approach?
- Hosting: local cron vs. cheap VPS vs. Fly.io?
- LLM provider/model for the reasoning layer?
