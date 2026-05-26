from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from paperader.models.paper import Paper, UserPaper
from paperader.models.user import User
from server.deps import get_db
from server.schemas.paper import PaperListOut, PaperOut, UserPaperUpdate

router = APIRouter(prefix="/api/papers", tags=["papers"])

DEFAULT_USER_ID = 1


@router.get("", response_model=PaperListOut)
def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: Optional[str] = None,
    venue: Optional[str] = None,
    year: Optional[int] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
    sort_by: str = Query("published_date", enum=["published_date", "created_at", "citation_count"]),
    db: Session = Depends(get_db),
):
    query = db.query(Paper)

    if source:
        query = query.filter(Paper.source == source)
    if venue:
        query = query.filter(Paper.venue.ilike(f"%{venue}%"))
    if year:
        query = query.filter(Paper.year == year)
    if category:
        query = query.filter(Paper.categories.cast(str).ilike(f"%{category}%"))
    if q:
        pattern = f"%{q}%"
        query = query.filter(Paper.title.ilike(pattern) | Paper.abstract.ilike(pattern))

    total = query.count()

    sort_col = getattr(Paper, sort_by)
    query = query.order_by(sort_col.desc().nullslast())

    papers = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaperListOut(
        papers=[PaperOut.model_validate(p) for p in papers],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return PaperOut.model_validate(paper)


@router.patch("/{paper_id}/user")
def update_user_paper(paper_id: int, data: UserPaperUpdate, db: Session = Depends(get_db)):
    paper = db.query(Paper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    user_paper = (
        db.query(UserPaper)
        .filter(UserPaper.user_id == DEFAULT_USER_ID, UserPaper.paper_id == paper_id)
        .first()
    )
    if not user_paper:
        user_paper = UserPaper(user_id=DEFAULT_USER_ID, paper_id=paper_id)
        db.add(user_paper)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user_paper, field, value)

    return {"status": "ok"}


@router.delete("/{paper_id}")
def delete_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    db.delete(paper)
    return {"status": "deleted"}
