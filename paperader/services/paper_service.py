from sqlalchemy.orm import Session

from paperader.collectors.base import PaperData
from paperader.models.paper import Paper


def upsert_papers(session: Session, papers: list[PaperData]) -> tuple[int, int]:
    added = 0
    updated = 0

    for p in papers:
        existing = None
        if p.arxiv_id:
            existing = session.query(Paper).filter(Paper.arxiv_id == p.arxiv_id).first()
        if not existing and p.doi:
            existing = session.query(Paper).filter(Paper.doi == p.doi).first()
        if not existing and not p.arxiv_id and not p.doi:
            existing = session.query(Paper).filter(Paper.title == p.title, Paper.year == p.year).first()

        if existing:
            if p.abstract and not existing.abstract:
                existing.abstract = p.abstract
            if p.venue and not existing.venue:
                existing.venue = p.venue
            if p.categories and not existing.categories:
                existing.categories = p.categories
            updated += 1
        else:
            paper = Paper(
                title=p.title,
                abstract=p.abstract,
                authors=p.authors,
                venue=p.venue,
                year=p.year,
                arxiv_id=p.arxiv_id,
                doi=p.doi,
                pdf_url=p.pdf_url,
                abs_url=p.abs_url,
                categories=p.categories,
                keywords=p.keywords,
                source=p.source,
                published_date=p.published_date,
            )
            session.add(paper)
            added += 1

    return added, updated


def search_papers(session: Session, query: str, limit: int = 20) -> list[Paper]:
    pattern = f"%{query}%"
    return (
        session.query(Paper)
        .filter(Paper.title.ilike(pattern) | Paper.abstract.ilike(pattern))
        .order_by(Paper.published_date.desc())
        .limit(limit)
        .all()
    )
