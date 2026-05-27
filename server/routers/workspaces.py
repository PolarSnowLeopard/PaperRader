from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from paperader.models.paper import Paper
from paperader.models.workspace import Folder, FolderPaper, Workspace
from server.deps import get_db
from server.schemas.paper import PaperOut
from server.schemas.workspace import WorkspaceCreate, WorkspaceOut, WorkspaceUpdate

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceOut])
def list_workspaces(db: Session = Depends(get_db)):
    workspaces = db.query(Workspace).order_by(Workspace.updated_at.desc()).all()
    results = []
    for ws in workspaces:
        folder_ids = [f.id for f in db.query(Folder.id).filter(Folder.workspace_id == ws.id).all()]
        paper_count = (
            db.query(func.count(func.distinct(FolderPaper.paper_id)))
            .filter(FolderPaper.folder_id.in_(folder_ids))
            .scalar()
            if folder_ids
            else 0
        )
        results.append(
            WorkspaceOut(
                id=ws.id,
                name=ws.name,
                description=ws.description,
                paper_count=paper_count,
                created_at=ws.created_at,
                updated_at=ws.updated_at,
            )
        )
    return results


@router.post("", response_model=WorkspaceOut)
def create_workspace(data: WorkspaceCreate, db: Session = Depends(get_db)):
    ws = Workspace(name=data.name, description=data.description)
    db.add(ws)
    db.flush()
    return WorkspaceOut(
        id=ws.id,
        name=ws.name,
        description=ws.description,
        paper_count=0,
        created_at=ws.created_at,
        updated_at=ws.updated_at,
    )


@router.get("/{workspace_id}", response_model=WorkspaceOut)
def get_workspace(workspace_id: int, db: Session = Depends(get_db)):
    ws = db.query(Workspace).get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    folder_ids = [f.id for f in db.query(Folder.id).filter(Folder.workspace_id == ws.id).all()]
    paper_count = (
        db.query(func.count(func.distinct(FolderPaper.paper_id)))
        .filter(FolderPaper.folder_id.in_(folder_ids))
        .scalar()
        if folder_ids
        else 0
    )
    return WorkspaceOut(
        id=ws.id,
        name=ws.name,
        description=ws.description,
        paper_count=paper_count,
        created_at=ws.created_at,
        updated_at=ws.updated_at,
    )


@router.get("/{workspace_id}/papers", response_model=list[PaperOut])
def list_workspace_papers(workspace_id: int, db: Session = Depends(get_db)):
    ws = db.query(Workspace).get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    folder_ids = [f.id for f in db.query(Folder.id).filter(Folder.workspace_id == ws.id).all()]
    if not folder_ids:
        return []
    paper_ids = [
        fp.paper_id
        for fp in db.query(FolderPaper.paper_id).filter(FolderPaper.folder_id.in_(folder_ids)).distinct().all()
    ]
    if not paper_ids:
        return []
    papers = db.query(Paper).filter(Paper.id.in_(paper_ids)).order_by(Paper.created_at.desc()).all()
    return [PaperOut.model_validate(p) for p in papers]


@router.patch("/{workspace_id}", response_model=WorkspaceOut)
def update_workspace(workspace_id: int, data: WorkspaceUpdate, db: Session = Depends(get_db)):
    ws = db.query(Workspace).get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if data.name is not None:
        ws.name = data.name
    if data.description is not None:
        ws.description = data.description
    db.flush()
    return WorkspaceOut(
        id=ws.id,
        name=ws.name,
        description=ws.description,
        paper_count=0,
        created_at=ws.created_at,
        updated_at=ws.updated_at,
    )


@router.delete("/{workspace_id}")
def delete_workspace(workspace_id: int, db: Session = Depends(get_db)):
    ws = db.query(Workspace).get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    db.query(Folder).filter(Folder.workspace_id == workspace_id).delete()
    db.delete(ws)
    return {"status": "deleted"}
