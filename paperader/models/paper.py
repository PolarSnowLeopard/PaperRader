from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from paperader.models.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    authors: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    venue: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    arxiv_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)
    doi: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    semantic_scholar_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    abs_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    categories: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    keywords: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    citation_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reference_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tldr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    influential_citation_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source: Mapped[str] = mapped_column(String(50), nullable=False, default="upload")
    published_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    __table_args__ = (
        Index("ix_papers_year_venue", "year", "venue"),
        Index("ix_papers_source", "source"),
        Index("ix_papers_published", "published_date"),
    )
