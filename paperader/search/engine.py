import time
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from paperader.models.paper import Paper
from paperader.search.filter_builder import build_query
from paperader.search.intent import SearchIntent, parse_intent
from paperader.search.ranker import RankedPaper, rerank_papers


@dataclass
class SearchResult:
    intent: SearchIntent
    results: list[RankedPaper] = field(default_factory=list)
    total_candidates: int = 0
    search_time_ms: int = 0


def semantic_search(
    session: Session,
    query: str,
    limit: int = 10,
    candidate_limit: int = 100,
) -> SearchResult:
    start_time = time.time()

    # Step 1: Parse intent via LLM
    intent = parse_intent(query)

    # Step 2: Build SQL query from intent
    base_query = session.query(Paper)
    filtered_query = build_query(base_query, intent)
    candidates = filtered_query.order_by(Paper.published_date.desc()).limit(candidate_limit).all()

    total_candidates = len(candidates)

    # Step 3: LLM re-ranking
    if candidates:
        ranked = rerank_papers(candidates, intent, top_k=limit)
    else:
        ranked = []

    elapsed_ms = int((time.time() - start_time) * 1000)

    return SearchResult(
        intent=intent,
        results=ranked,
        total_candidates=total_candidates,
        search_time_ms=elapsed_ms,
    )
