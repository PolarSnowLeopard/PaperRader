from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from paperader.collectors.arxiv import ArxivCollector
from paperader.collectors.dblp import DblpCollector
from paperader.models.sync_log import SyncLog
from paperader.models.user import UserSubscription
from paperader.services.paper_service import upsert_papers
from server.deps import get_db

router = APIRouter(prefix="/api/sync", tags=["sync"])

DEFAULT_USER_ID = 1


def _run_arxiv_sync(categories: list[str], max_results: int = 100):
    from paperader.models.base import get_session

    with get_session() as session:
        log = SyncLog(source="arxiv", status="running")
        session.add(log)
        session.flush()

        try:
            collector = ArxivCollector(max_results=max_results)
            papers = collector.collect(categories=categories or None)
            added, updated = upsert_papers(session, papers)
            log.status = "success"
            log.papers_added = added
            log.papers_updated = updated
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
        finally:
            log.finished_at = datetime.now(timezone.utc)


@router.post("/arxiv")
def trigger_arxiv_sync(
    background_tasks: BackgroundTasks,
    max_results: int = 100,
    db: Session = Depends(get_db),
):
    subs = (
        db.query(UserSubscription)
        .filter(
            UserSubscription.user_id == DEFAULT_USER_ID,
            UserSubscription.sub_type == "category",
        )
        .all()
    )
    categories = [s.value for s in subs]

    background_tasks.add_task(_run_arxiv_sync, categories, max_results)
    return {"status": "started", "source": "arxiv", "categories": categories}


@router.post("/dblp")
def trigger_dblp_sync(
    background_tasks: BackgroundTasks,
    max_results: int = 100,
    db: Session = Depends(get_db),
):
    subs = (
        db.query(UserSubscription)
        .filter(
            UserSubscription.user_id == DEFAULT_USER_ID,
            UserSubscription.sub_type == "conference",
        )
        .all()
    )
    conferences = [s.value for s in subs]

    if not conferences:
        return {"status": "skipped", "reason": "No conference subscriptions"}

    # Run inline since DBLP is fast
    current_year = datetime.now(timezone.utc).year
    collector = DblpCollector(max_results=max_results)
    total_added = 0

    for conf in conferences:
        for yr in range(current_year, current_year - 3, -1):
            batch = collector.search_conference(conf, year=yr)
            if batch:
                added, _ = upsert_papers(db, batch)
                total_added += added
                break

    return {"status": "done", "papers_added": total_added, "conferences": conferences}


@router.get("/logs")
def get_sync_logs(limit: int = 20, db: Session = Depends(get_db)):
    logs = db.query(SyncLog).order_by(SyncLog.started_at.desc()).limit(limit).all()
    return [
        {
            "id": log.id,
            "source": log.source,
            "status": log.status,
            "papers_added": log.papers_added,
            "papers_updated": log.papers_updated,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "finished_at": log.finished_at.isoformat() if log.finished_at else None,
            "error_message": log.error_message,
        }
        for log in logs
    ]
