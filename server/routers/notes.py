from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from paperader.models.note import PaperNote
from server.deps import get_db
from server.schemas.workspace import NoteOut, NoteUpdate

router = APIRouter(prefix="/api/papers", tags=["notes"])


@router.get("/{paper_id}/notes", response_model=NoteOut | None)
def get_note(paper_id: int, workspace_id: int, db: Session = Depends(get_db)):
    note = (
        db.query(PaperNote)
        .filter(PaperNote.paper_id == paper_id, PaperNote.workspace_id == workspace_id)
        .first()
    )
    if not note:
        return None
    return NoteOut.model_validate(note)


@router.put("/{paper_id}/notes", response_model=NoteOut)
def save_note(paper_id: int, data: NoteUpdate, db: Session = Depends(get_db)):
    note = (
        db.query(PaperNote)
        .filter(PaperNote.paper_id == paper_id, PaperNote.workspace_id == data.workspace_id)
        .first()
    )
    if note:
        note.content = data.content
    else:
        note = PaperNote(paper_id=paper_id, workspace_id=data.workspace_id, content=data.content)
        db.add(note)
    db.flush()
    return NoteOut.model_validate(note)
