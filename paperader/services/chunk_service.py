"""PDF text extraction and chunking service."""

from pathlib import Path

from sqlalchemy.orm import Session

from paperader.config import get_settings
from paperader.models.chunk import PaperChunk


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """Extract text from PDF, returns list of {page_num, text}."""
    import fitz

    full_path = Path(get_settings().pdf_storage_path) / pdf_path
    if not full_path.exists():
        return []

    doc = fitz.open(str(full_path))
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages.append({"page_num": page_num + 1, "text": text.strip()})
    doc.close()
    return pages


def chunk_text(pages: list[dict], max_tokens: int = 500) -> list[dict]:
    """Split page texts into ~max_tokens chunks (approx 4 chars/token)."""
    max_chars = max_tokens * 4
    chunks = []

    for page_info in pages:
        text = page_info["text"]
        page_num = page_info["page_num"]

        paragraphs = text.split("\n\n")
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= max_chars:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para
            else:
                if current_chunk:
                    chunks.append({"content": current_chunk, "page_num": page_num})
                if len(para) > max_chars:
                    for i in range(0, len(para), max_chars):
                        chunks.append({"content": para[i:i + max_chars], "page_num": page_num})
                    current_chunk = ""
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append({"content": current_chunk, "page_num": page_num})

    return chunks


def index_paper_chunks(db: Session, paper_id: int, pdf_path: str) -> int:
    """Extract text from PDF and store as chunks. Returns chunk count."""
    db.query(PaperChunk).filter(PaperChunk.paper_id == paper_id).delete()

    pages = extract_text_from_pdf(pdf_path)
    if not pages:
        return 0

    chunks = chunk_text(pages)
    for idx, chunk in enumerate(chunks):
        db.add(PaperChunk(
            paper_id=paper_id,
            chunk_index=idx,
            content=chunk["content"],
            page_num=chunk["page_num"],
        ))

    db.flush()
    return len(chunks)
