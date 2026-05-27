from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from paperader.models.tag import PaperTag, Tag
from paperader.models.workspace import Workspace
from server.deps import get_db
from server.schemas.workspace import TagCreate, TagOut, TagUpdate

router = APIRouter(tags=["tags"])


@router.get("/api/workspaces/{workspace_id}/tags", response_model=list[TagOut])
def list_tags(workspace_id: int, db: Session = Depends(get_db)):
    ws = db.query(Workspace).get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    tags = db.query(Tag).filter(Tag.workspace_id == workspace_id).all()
    return [TagOut.model_validate(t) for t in tags]


@router.post("/api/workspaces/{workspace_id}/tags", response_model=TagOut)
def create_tag(workspace_id: int, data: TagCreate, db: Session = Depends(get_db)):
    ws = db.query(Workspace).get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    tag = Tag(workspace_id=workspace_id, name=data.name, color=data.color)
    db.add(tag)
    db.flush()
    return TagOut.model_validate(tag)


@router.patch("/api/tags/{tag_id}", response_model=TagOut)
def update_tag(tag_id: int, data: TagUpdate, db: Session = Depends(get_db)):
    tag = db.query(Tag).get(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if data.name is not None:
        tag.name = data.name
    if data.color is not None:
        tag.color = data.color
    db.flush()
    return TagOut.model_validate(tag)


@router.delete("/api/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).get(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.query(PaperTag).filter(PaperTag.tag_id == tag_id).delete()
    db.delete(tag)
    return {"status": "deleted"}


@router.post("/api/papers/{paper_id}/tags")
def add_tag_to_paper(paper_id: int, tag_id: int, db: Session = Depends(get_db)):
    existing = (
        db.query(PaperTag)
        .filter(PaperTag.paper_id == paper_id, PaperTag.tag_id == tag_id)
        .first()
    )
    if existing:
        return {"status": "already_exists"}
    db.add(PaperTag(paper_id=paper_id, tag_id=tag_id))
    return {"status": "added"}


@router.delete("/api/papers/{paper_id}/tags/{tag_id}")
def remove_tag_from_paper(paper_id: int, tag_id: int, db: Session = Depends(get_db)):
    pt = (
        db.query(PaperTag)
        .filter(PaperTag.paper_id == paper_id, PaperTag.tag_id == tag_id)
        .first()
    )
    if not pt:
        raise HTTPException(status_code=404, detail="Tag not on paper")
    db.delete(pt)
    return {"status": "removed"}
