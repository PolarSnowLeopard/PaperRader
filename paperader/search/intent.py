from dataclasses import dataclass, field
from datetime import datetime, timezone

from paperader.llm.client import get_json_completion
from paperader.llm.prompts import INTENT_SYSTEM, INTENT_USER_TEMPLATE


@dataclass
class SearchIntent:
    topics: list[str] = field(default_factory=list)
    keywords_sql: list[str] = field(default_factory=list)
    venues: list[str] | None = None
    year_min: int | None = None
    year_max: int | None = None
    categories: list[str] | None = None
    authors: list[str] | None = None
    intent_summary: str = ""


def parse_intent(query: str) -> SearchIntent:
    current_year = datetime.now(timezone.utc).year
    prompt = INTENT_USER_TEMPLATE.format(query=query, current_year=current_year)

    result = get_json_completion(prompt=prompt, system=INTENT_SYSTEM)

    return SearchIntent(
        topics=result.get("topics", []),
        keywords_sql=result.get("keywords_sql", []),
        venues=result.get("venues"),
        year_min=result.get("year_min"),
        year_max=result.get("year_max"),
        categories=result.get("categories"),
        authors=result.get("authors"),
        intent_summary=result.get("intent_summary", query),
    )
