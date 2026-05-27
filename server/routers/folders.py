from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from paperader.models.paper import Paper
from paperader.models.workspace import Folder, FolderPaper, Workspace
from server.deps import get_db
from server.schemas.paper import PaperOut
from server.schemas.workspace import FolderCreate, FolderOut, FolderUpdate

router = APIRouter(tags=["folders"])


def _build_folder_tree(folders: list[Folder], parent_id: Optional[int] = None) -> list[FolderOut]:
    tree = []
    for f in folders:
        if f.parent_id == parent_id:
            children = _build_folder_tree(folders, f.id)
            tree.append(
                FolderOut(
                    id=f.id,
                    workspace_id=f.workspace_id,
                    parent_id=f.parent_id,
                    name=f.name,
                    sort_order=f.sort_order,
                    children=children,
                )
            )
    tree.sort(key=lambda x: x.sort_order)
    return tree


@router.get("/api/workspaces/{workspace_id}/folders", response_model=list[FolderOut])
def get_folder_tree(workspace_id: int, db: Session = Depends(get_db)):
    ws = db.query(Workspace).get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    folders = db.query(Folder).filter(Folder.workspace_id == workspace_id).all()
    return _build_folder_tree(folders)


@router.post("/api/workspaces/{workspace_id}/folders", response_model=FolderOut)
def create_folder(workspace_id: int, data: FolderCreate, db: Session = Depends(get_db)):
    ws = db.query(Workspace).get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if data.parent_id:
        parent = db.query(Folder).get(data.parent_id)
        if not parent or parent.workspace_id != workspace_id:
            raise HTTPException(status_code=400, detail="Invalid parent folder")
    folder = Folder(workspace_id=workspace_id, parent_id=data.parent_id, name=data.name)
    db.add(folder)
    db.flush()
    return FolderOut(
        id=folder.id,
        workspace_id=folder.workspace_id,
        parent_id=folder.parent_id,
        name=folder.name,
        sort_order=folder.sort_order,
        children=[],
    )


@router.patch("/api/folders/{folder_id}", response_model=FolderOut)
def update_folder(folder_id: int, data: FolderUpdate, db: Session = Depends(get_db)):
    folder = db.query(Folder).get(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    if data.name is not None:
        folder.name = data.name
    if data.parent_id is not None:
        folder.parent_id = data.parent_id
    if data.sort_order is not None:
        folder.sort_order = data.sort_order
    db.flush()
    return FolderOut(
        id=folder.id,
        workspace_id=folder.workspace_id,
        parent_id=folder.parent_id,
        name=folder.name,
        sort_order=folder.sort_order,
        children=[],
    )


@router.delete("/api/folders/{folder_id}")
def delete_folder(folder_id: int, db: Session = Depends(get_db)):
    folder = db.query(Folder).get(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    _delete_folder_recursive(db, folder_id)
    db.delete(folder)
    return {"status": "deleted"}


def _delete_folder_recursive(db: Session, folder_id: int):
    children = db.query(Folder).filter(Folder.parent_id == folder_id).all()
    for child in children:
        _delete_folder_recursive(db, child.id)
        db.delete(child)
    db.query(FolderPaper).filter(FolderPaper.folder_id == folder_id).delete()


@router.get("/api/folders/{folder_id}/papers", response_model=list[PaperOut])
def list_folder_papers(folder_id: int, db: Session = Depends(get_db)):
    folder = db.query(Folder).get(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    paper_ids = [
        fp.paper_id
        for fp in db.query(FolderPaper).filter(FolderPaper.folder_id == folder_id).all()
    ]
    if not paper_ids:
        return []
    papers = db.query(Paper).filter(Paper.id.in_(paper_ids)).all()
    return [PaperOut.model_validate(p) for p in papers]


@router.post("/api/folders/{folder_id}/papers")
def add_paper_to_folder(folder_id: int, paper_id: int, db: Session = Depends(get_db)):
    folder = db.query(Folder).get(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    paper = db.query(Paper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    existing = (
        db.query(FolderPaper)
        .filter(FolderPaper.folder_id == folder_id, FolderPaper.paper_id == paper_id)
        .first()
    )
    if existing:
        return {"status": "already_exists"}
    db.add(FolderPaper(folder_id=folder_id, paper_id=paper_id))
    return {"status": "added"}


@router.delete("/api/folders/{folder_id}/papers/{paper_id}")
def remove_paper_from_folder(folder_id: int, paper_id: int, db: Session = Depends(get_db)):
    fp = (
        db.query(FolderPaper)
        .filter(FolderPaper.folder_id == folder_id, FolderPaper.paper_id == paper_id)
        .first()
    )
    if not fp:
        raise HTTPException(status_code=404, detail="Paper not in folder")
    db.delete(fp)
    return {"status": "removed"}
