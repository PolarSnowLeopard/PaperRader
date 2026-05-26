from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from paperader.search.engine import semantic_search
from server.deps import get_db
from server.schemas.paper import PaperOut
from server.schemas.search import SearchRequest, SearchResponse, SearchResultItem

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search_papers(req: SearchRequest, db: Session = Depends(get_db)):
    result = semantic_search(db, req.query, limit=req.limit)

    items = [
        SearchResultItem(
            paper=PaperOut.model_validate(r.paper),
            score=r.score,
            reason=r.reason,
        )
        for r in result.results
    ]

    return SearchResponse(
        query_interpretation=result.intent.intent_summary,
        results=items,
        total_candidates=result.total_candidates,
        search_time_ms=result.search_time_ms,
    )
