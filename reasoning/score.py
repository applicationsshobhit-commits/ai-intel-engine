import json
import re
from datetime import datetime, timezone

from reasoning.llm import call_llm

PROMPT_TEMPLATE = """You are scoring a news item for relevance to a list of tracked entities,
for a reader who works in enterprise software/CRM (Salesforce ecosystem) and wants signal
on competitive moves, investment/stock activity, and product innovation.
Be strict: only include an entity if the item is substantively ABOUT that entity
(its products, decisions, or actions) — not merely adjacent to the same industry.
When in doubt, leave the entity out.

Entities: {entities}

Item title: {title}
Item content: {content}

For each relevant entity, write a summary under 15 words that leads with WHY it matters
(competitive threat, investment signal, innovation) rather than restating the headline.

Respond with ONLY a JSON array, no other text, like:
[{{"entity": "OpenAI", "relevance_score": 0.9, "summary": "under 15 words, why it matters"}}]
If no entities are substantively relevant, respond with: []"""


def score_item(item: dict, entity_names: list) -> list:
    prompt = PROMPT_TEMPLATE.format(
        entities=", ".join(entity_names),
        title=item["title"],
        content=(item["content"] or "")[:1500],
    )
    raw = call_llm(prompt)

    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return []
    try:
        results = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []

    now = datetime.now(timezone.utc).isoformat()
    valid = []
    for r in results:
        if not isinstance(r, dict) or "entity" not in r:
            continue
        r["created_at"] = now
        valid.append(r)
    return valid
