from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from paperader.config import get_settings
from paperader.models.chunk import PaperChunk
from paperader.models.paper import Paper
from paperader.models.tag import PaperTag
from paperader.services.chunk_service import index_paper_chunks
from paperader.services.import_service import (
    download_pdf,
    fetch_arxiv_metadata,
    fetch_doi_metadata,
    save_pdf_file,
)
from server.deps import get_db
from server.schemas.paper import PaperListOut, PaperOut

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.get("", response_model=PaperListOut)
def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: Optional[str] = None,
    venue: Optional[str] = None,
    year: Optional[int] = None,
    q: Optional[str] = None,
    sort_by: str = Query("created_at", enum=["published_date", "created_at", "citation_count", "year"]),
    db: Session = Depends(get_db),
):
    query = db.query(Paper)

    if source:
        query = query.filter(Paper.source == source)
    if venue:
        query = query.filter(Paper.venue.ilike(f"%{venue}%"))
    if year:
        query = query.filter(Paper.year == year)
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


@router.get("/{paper_id}/pdf")
def get_paper_pdf(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).get(paper_id)
    if not paper or not paper.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not found")
    pdf_file = Path(get_settings().pdf_storage_path) / paper.pdf_path
    if not pdf_file.exists():
        raise HTTPException(status_code=404, detail="PDF file missing")
    return FileResponse(pdf_file, media_type="application/pdf", headers={"Content-Disposition": "inline"})


@router.post("/upload", response_model=PaperOut)
def upload_paper(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

    content = file.file.read()
    filename = save_pdf_file(content)

    paper_title = title or file.filename.rsplit(".", 1)[0]
    paper = Paper(title=paper_title, pdf_path=filename, source="upload")
    db.add(paper)
    db.flush()
    index_paper_chunks(db, paper.id, filename)
    return PaperOut.model_validate(paper)


@router.post("/{paper_id}/download-pdf", response_model=PaperOut)
def download_paper_pdf(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    if paper.pdf_path:
        return PaperOut.model_validate(paper)
    if not paper.pdf_url:
        raise HTTPException(status_code=400, detail="No PDF URL available")
    pdf_content = download_pdf(paper.pdf_url)
    if not pdf_content:
        raise HTTPException(status_code=502, detail="Failed to download PDF")
    name_hint = None
    if paper.arxiv_id:
        name_hint = f"{paper.arxiv_id.replace('/', '_')}.pdf"
    filename = save_pdf_file(pdf_content, name_hint)
    paper.pdf_path = filename
    db.flush()
    index_paper_chunks(db, paper.id, filename)
    return PaperOut.model_validate(paper)


class ImportRequest(BaseModel):
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None


@router.post("/import", response_model=PaperOut)
def import_paper(data: ImportRequest, db: Session = Depends(get_db)):
    if not data.arxiv_id and not data.doi:
        raise HTTPException(status_code=400, detail="Provide arxiv_id or doi")

    if data.arxiv_id:
        existing = db.query(Paper).filter(Paper.arxiv_id == data.arxiv_id).first()
        if existing:
            return PaperOut.model_validate(existing)

        meta = fetch_arxiv_metadata(data.arxiv_id)
        if not meta:
            raise HTTPException(status_code=404, detail="Paper not found on arXiv")

        paper = Paper(
            title=meta.title,
            abstract=meta.abstract,
            authors=meta.authors,
            year=meta.year,
            arxiv_id=meta.arxiv_id,
            pdf_url=meta.pdf_url,
            abs_url=meta.abs_url,
            categories=meta.categories,
            source=meta.source,
            published_date=meta.published_date,
        )

        if meta.pdf_url:
            pdf_content = download_pdf(meta.pdf_url)
            if pdf_content:
                filename = save_pdf_file(pdf_content, f"{meta.arxiv_id.replace('/', '_')}.pdf")
                paper.pdf_path = filename

        db.add(paper)
        db.flush()
        if paper.pdf_path:
            index_paper_chunks(db, paper.id, paper.pdf_path)
        return PaperOut.model_validate(paper)

    if data.doi:
        existing = db.query(Paper).filter(Paper.doi == data.doi).first()
        if existing:
            return PaperOut.model_validate(existing)

        meta = fetch_doi_metadata(data.doi)
        if not meta:
            raise HTTPException(status_code=404, detail="Paper not found via DOI")

        paper = Paper(
            title=meta.title,
            abstract=meta.abstract,
            authors=meta.authors,
            venue=meta.venue,
            year=meta.year,
            doi=meta.doi,
            pdf_url=meta.pdf_url,
            source=meta.source,
        )

        if meta.pdf_url:
            pdf_content = download_pdf(meta.pdf_url)
            if pdf_content:
                filename = save_pdf_file(pdf_content)
                paper.pdf_path = filename

        db.add(paper)
        db.flush()
        if paper.pdf_path:
            index_paper_chunks(db, paper.id, paper.pdf_path)
        return PaperOut.model_validate(paper)


@router.delete("/{paper_id}")
def delete_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    if paper.pdf_path:
        pdf_file = Path(get_settings().pdf_storage_path) / paper.pdf_path
        if pdf_file.exists():
            pdf_file.unlink()
    db.query(PaperChunk).filter(PaperChunk.paper_id == paper_id).delete()
    db.query(PaperTag).filter(PaperTag.paper_id == paper_id).delete()
    db.delete(paper)
    return {"status": "deleted"}
