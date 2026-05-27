from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from paperader.models.chat import ChatMessage, ChatSession
from paperader.services.chat_service import chat_answer
from server.deps import get_db

router = APIRouter(prefix="/api", tags=["chat"])


class SessionCreate(BaseModel):
    title: Optional[str] = "New Chat"


class SessionOut(BaseModel):
    id: int
    workspace_id: int
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    referenced_papers: Optional[list] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str


@router.get("/workspaces/{ws_id}/chat", response_model=list[SessionOut])
def list_sessions(ws_id: int, db: Session = Depends(get_db)):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.workspace_id == ws_id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return [SessionOut.model_validate(s) for s in sessions]


@router.post("/workspaces/{ws_id}/chat", response_model=SessionOut)
def create_session(ws_id: int, data: SessionCreate, db: Session = Depends(get_db)):
    session = ChatSession(workspace_id=ws_id, title=data.title or "New Chat")
    db.add(session)
    db.flush()
    return SessionOut.model_validate(session)


@router.delete("/chat/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).get(session_id)
    if not session:
        raise HTTPException(status_code=404)
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    return {"status": "deleted"}


@router.get("/chat/{session_id}/messages", response_model=list[MessageOut])
def get_messages(session_id: int, db: Session = Depends(get_db)):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [MessageOut.model_validate(m) for m in messages]


@router.post("/chat/{session_id}/messages", response_model=MessageOut)
def send_message(session_id: int, data: MessageCreate, db: Session = Depends(get_db)):
    session = db.query(ChatSession).get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=data.content,
    )
    db.add(user_msg)
    db.flush()

    if session.title == "New Chat":
        session.title = data.content[:30] + ("..." if len(data.content) > 30 else "")

    answer, ref_ids = chat_answer(db, session_id, data.content)

    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=answer,
        referenced_papers=ref_ids if ref_ids else None,
    )
    db.add(assistant_msg)
    db.flush()

    return MessageOut.model_validate(assistant_msg)
