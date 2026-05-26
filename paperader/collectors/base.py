from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PaperData:
    title: str
    source: str
    abstract: Optional[str] = None
    authors: list[str] = field(default_factory=list)
    venue: Optional[str] = None
    year: Optional[int] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    pdf_url: Optional[str] = None
    abs_url: Optional[str] = None
    categories: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    published_date: Optional[datetime] = None


class BaseCollector(ABC):
    @abstractmethod
    def collect(self, categories: list[str] | None = None, **kwargs) -> list[PaperData]:
        ...
