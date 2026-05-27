from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class WorkspaceOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    paper_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None


class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


class FolderOut(BaseModel):
    id: int
    workspace_id: int
    parent_id: Optional[int] = None
    name: str
    sort_order: int = 0
    children: list["FolderOut"] = []

    class Config:
        from_attributes = True


class TagCreate(BaseModel):
    name: str
    color: Optional[str] = None


class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


class TagOut(BaseModel):
    id: int
    workspace_id: int
    name: str
    color: Optional[str] = None

    class Config:
        from_attributes = True


class NoteUpdate(BaseModel):
    content: str
    workspace_id: int


class NoteOut(BaseModel):
    id: int
    paper_id: int
    workspace_id: int
    content: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True
