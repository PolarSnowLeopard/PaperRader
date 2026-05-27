from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from paperader.models.workspace import Folder, FolderPaper
from paperader.search.engine import semantic_search
from paperader.services.external_search import search_arxiv, search_semantic_scholar
from server.deps import get_db
from server.schemas.paper import PaperOut
from server.schemas.search import SearchRequest, SearchResponse, SearchResultItem

router = APIRouter(prefix="/api/search", tags=["search"])


def _get_workspace_paper_ids(db: Session, workspace_id: int) -> list[int]:
    folder_ids = [
        f.id for f in db.query(Folder.id).filter(Folder.workspace_id == workspace_id).all()
    ]
    if not folder_ids:
        return []
    return [
        fp.paper_id for fp in
        db.query(FolderPaper.paper_id).filter(FolderPaper.folder_id.in_(folder_ids)).distinct().all()
    ]


@router.post("", response_model=SearchResponse)
def search_papers(req: SearchRequest, db: Session = Depends(get_db)):
    paper_ids = None
    if req.workspace_id:
        paper_ids = _get_workspace_paper_ids(db, req.workspace_id)
        if not paper_ids:
            return SearchResponse(
                query_interpretation="工作空间内暂无论文",
                results=[],
                total_candidates=0,
                search_time_ms=0,
            )

    result = semantic_search(db, req.query, limit=req.limit, paper_ids=paper_ids)

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


class ExternalSearchRequest(BaseModel):
    query: str
    source: str = "arxiv"
    limit: int = 20


class ExternalPaperItem(BaseModel):
    title: str
    authors: list[str] = []
    abstract: Optional[str] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    categories: list[str] = []
    citation_count: Optional[int] = None
    source: str


class ExternalSearchResponse(BaseModel):
    results: list[ExternalPaperItem]
    total: int


@router.post("/external", response_model=ExternalSearchResponse)
def external_search(req: ExternalSearchRequest):
    if req.source == "semantic_scholar":
        results = search_semantic_scholar(req.query, limit=req.limit)
    else:
        results = search_arxiv(req.query, max_results=req.limit)

    items = [ExternalPaperItem(**r) for r in results]
    return ExternalSearchResponse(results=items, total=len(items))
