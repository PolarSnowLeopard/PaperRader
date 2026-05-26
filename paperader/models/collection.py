from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from paperader.models.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    collection_type: Mapped[str] = mapped_column(String(50), nullable=False)  # daily, conference, manual
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("ix_collection_user", "user_id"),
    )


class PaperCollection(Base):
    __tablename__ = "paper_collections"

    paper_id: Mapped[int] = mapped_column(Integer, ForeignKey("papers.id"), primary_key=True)
    collection_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("collections.id"), primary_key=True
    )
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
