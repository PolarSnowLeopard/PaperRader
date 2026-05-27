from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from paperader.models.sync_log import SyncLog
from paperader.services.paper_service import upsert_papers
from server.deps import get_db

router = APIRouter(prefix="/api/sync", tags=["sync"])


def _run_arxiv_sync(categories: list[str] | None, max_results: int = 100):
    from paperader.collectors.arxiv import ArxivCollector
    from paperader.models.base import get_session

    with get_session() as session:
        log = SyncLog(source="arxiv", status="running")
        session.add(log)
        session.flush()
        try:
            collector = ArxivCollector(max_results=max_results)
            papers = collector.collect(categories=categories)
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
    categories: str = "cs.CL,cs.AI,cs.LG",
    max_results: int = 100,
):
    cat_list = [c.strip() for c in categories.split(",") if c.strip()]
    background_tasks.add_task(_run_arxiv_sync, cat_list, max_results)
    return {"status": "started", "source": "arxiv", "categories": cat_list}


@router.post("/dblp")
def trigger_dblp_sync(
    conference: str = "NeurIPS",
    max_results: int = 100,
    db: Session = Depends(get_db),
):
    from paperader.collectors.dblp import DblpCollector

    current_year = datetime.now(timezone.utc).year
    collector = DblpCollector(max_results=max_results)
    papers = []
    for yr in range(current_year, current_year - 3, -1):
        batch = collector.search_conference(conference, year=yr)
        if batch:
            papers.extend(batch)
            break

    if papers:
        added, _ = upsert_papers(db, papers)
        return {"status": "done", "papers_added": added, "conference": conference}
    return {"status": "done", "papers_added": 0, "conference": conference}


@router.post("/openreview")
def trigger_openreview_sync(
    background_tasks: BackgroundTasks,
    conference: str = "ICLR2025",
    max_results: int = 200,
):
    def _run():
        from paperader.collectors.openreview import OpenReviewCollector
        from paperader.models.base import get_session

        with get_session() as session:
            log = SyncLog(source="openreview", status="running")
            session.add(log)
            session.flush()
            try:
                collector = OpenReviewCollector(max_results=max_results)
                papers = collector.get_accepted_papers(conference)
                added, updated = upsert_papers(session, papers)
                log.status = "success"
                log.papers_added = added
                log.papers_updated = updated
            except Exception as e:
                log.status = "failed"
                log.error_message = str(e)
            finally:
                log.finished_at = datetime.now(timezone.utc)

    background_tasks.add_task(_run)
    return {"status": "started", "source": "openreview", "conference": conference}


@router.post("/acl")
def trigger_acl_sync(
    background_tasks: BackgroundTasks,
    conference: str = "ACL2024",
    max_results: int = 200,
):
    def _run():
        from paperader.collectors.acl_anthology import AclAnthologyCollector
        from paperader.models.base import get_session

        with get_session() as session:
            log = SyncLog(source="acl_anthology", status="running")
            session.add(log)
            session.flush()
            try:
                collector = AclAnthologyCollector(max_results=max_results)
                papers = collector.get_conference_papers(conference)
                added, updated = upsert_papers(session, papers)
                log.status = "success"
                log.papers_added = added
                log.papers_updated = updated
            except Exception as e:
                log.status = "failed"
                log.error_message = str(e)
            finally:
                log.finished_at = datetime.now(timezone.utc)

    background_tasks.add_task(_run)
    return {"status": "started", "source": "acl_anthology", "conference": conference}


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


@router.get("/conference-stats")
def get_conference_stats(venue: str, db: Session = Depends(get_db)):
    """Get statistics for papers from a specific conference/venue."""
    from collections import Counter

    from paperader.models.paper import Paper

    papers = db.query(Paper).filter(Paper.venue.ilike(f"%{venue}%")).all()
    if not papers:
        return {"venue": venue, "total": 0, "categories": {}, "top_authors": [], "year_dist": {}}

    all_categories = []
    all_authors = []
    year_dist = Counter()

    for p in papers:
        if p.categories:
            all_categories.extend(p.categories)
        if p.authors:
            all_authors.extend(p.authors[:3])
        if p.year:
            year_dist[str(p.year)] += 1

    cat_counts = Counter(all_categories).most_common(15)
    author_counts = Counter(all_authors).most_common(20)

    return {
        "venue": venue,
        "total": len(papers),
        "categories": dict(cat_counts),
        "top_authors": [{"name": name, "count": cnt} for name, cnt in author_counts],
        "year_dist": dict(year_dist),
    }


@router.post("/batch-import")
def batch_import_to_workspace(
    venue: str,
    folder_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Import conference papers into a workspace folder."""
    from paperader.models.paper import Paper
    from paperader.models.workspace import FolderPaper

    papers = (
        db.query(Paper)
        .filter(Paper.venue.ilike(f"%{venue}%"))
        .order_by(Paper.citation_count.desc().nullslast())
        .limit(limit)
        .all()
    )

    imported = 0
    for paper in papers:
        exists = db.query(FolderPaper).filter(
            FolderPaper.folder_id == folder_id,
            FolderPaper.paper_id == paper.id,
        ).first()
        if not exists:
            db.add(FolderPaper(folder_id=folder_id, paper_id=paper.id))
            imported += 1

    db.flush()
    return {"status": "done", "imported": imported, "total_available": len(papers)}
