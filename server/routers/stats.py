from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from paperader.models.paper import Paper, UserPaper
from server.deps import get_db
from server.schemas.stats import (
    OverviewStats,
    TopicCount,
    TopicsResponse,
    TrendPoint,
    TrendsResponse,
    VenueCount,
    VenuesResponse,
)

router = APIRouter(prefix="/api/stats", tags=["stats"])

DEFAULT_USER_ID = 1


@router.get("/overview", response_model=OverviewStats)
def overview(db: Session = Depends(get_db)):
    total = db.query(func.count(Paper.id)).scalar() or 0

    sources = dict(
        db.query(Paper.source, func.count(Paper.id)).group_by(Paper.source).all()
    )

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_week = (
        db.query(func.count(Paper.id)).filter(Paper.created_at >= week_ago).scalar() or 0
    )

    starred = (
        db.query(func.count(UserPaper.id))
        .filter(UserPaper.user_id == DEFAULT_USER_ID, UserPaper.is_starred.is_(True))
        .scalar()
        or 0
    )

    return OverviewStats(
        total_papers=total,
        sources=sources,
        recent_week=recent_week,
        starred_count=starred,
    )


@router.get("/trends", response_model=TrendsResponse)
def trends(days: int = Query(30, ge=7, le=365), db: Session = Depends(get_db)):
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    rows = (
        db.query(func.date(Paper.created_at), func.count(Paper.id))
        .filter(Paper.created_at >= start_date)
        .group_by(func.date(Paper.created_at))
        .order_by(func.date(Paper.created_at))
        .all()
    )

    return TrendsResponse(daily=[TrendPoint(date=str(d), count=c) for d, c in rows])


@router.get("/topics", response_model=TopicsResponse)
def topics(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    # Extract keywords from papers' categories (simple approach)
    papers = db.query(Paper.categories).filter(Paper.categories.isnot(None)).all()

    counts: dict[str, int] = {}
    for (cats,) in papers:
        if cats:
            for cat in cats:
                counts[cat] = counts.get(cat, 0) + 1

    sorted_topics = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    return TopicsResponse(topics=[TopicCount(topic=t, count=c) for t, c in sorted_topics])


@router.get("/venues", response_model=VenuesResponse)
def venues(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    rows = (
        db.query(Paper.venue, func.count(Paper.id))
        .filter(Paper.venue.isnot(None))
        .group_by(Paper.venue)
        .order_by(func.count(Paper.id).desc())
        .limit(limit)
        .all()
    )

    return VenuesResponse(venues=[VenueCount(venue=v, count=c) for v, c in rows])
