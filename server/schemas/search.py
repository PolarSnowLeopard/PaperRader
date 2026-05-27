from typing import Optional

from pydantic import BaseModel

from server.schemas.paper import PaperOut


class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    workspace_id: Optional[int] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    venues: Optional[list[str]] = None


class SearchResultItem(BaseModel):
    paper: PaperOut
    score: float
    reason: str


class SearchResponse(BaseModel):
    query_interpretation: str
    results: list[SearchResultItem]
    total_candidates: int
    search_time_ms: int
