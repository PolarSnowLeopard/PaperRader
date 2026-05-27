from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PaperOut(BaseModel):
    id: int
    title: str
    abstract: Optional[str] = None
    authors: list[str] = []
    venue: Optional[str] = None
    year: Optional[int] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    pdf_path: Optional[str] = None
    pdf_url: Optional[str] = None
    abs_url: Optional[str] = None
    categories: list[str] = []
    tags: list[str] = []
    keywords: list[str] = []
    citation_count: Optional[int] = None
    tldr: Optional[str] = None
    report: Optional[str] = None
    source: str
    published_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaperListOut(BaseModel):
    papers: list[PaperOut]
    total: int
    page: int
    page_size: int
