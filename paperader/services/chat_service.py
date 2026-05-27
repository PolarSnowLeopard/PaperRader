"""Chat RAG service — cross-paper Q&A within a workspace."""

from sqlalchemy.orm import Session

from paperader.llm.client import get_completion
from paperader.models.chat import ChatMessage, ChatSession
from paperader.models.chunk import PaperChunk
from paperader.models.paper import Paper
from paperader.models.workspace import FolderPaper, Folder


CHAT_SYSTEM = """你是一个科研助手，帮助用户分析和理解工作空间中的论文集合。
你可以访问工作空间内多篇论文的内容。根据提供的论文片段回答用户问题。

回答要求：
- 使用中文
- 引用具体论文时用【论文标题】标注
- 如果信息不足以回答，诚实说明
- 保持学术严谨性，不编造信息"""


def get_workspace_paper_ids(db: Session, workspace_id: int) -> list[int]:
    """Get all paper IDs in a workspace (across all folders)."""
    folder_ids = [
        f.id for f in db.query(Folder.id).filter(Folder.workspace_id == workspace_id).all()
    ]
    if not folder_ids:
        return []
    paper_ids = [
        fp.paper_id for fp in
        db.query(FolderPaper.paper_id).filter(FolderPaper.folder_id.in_(folder_ids)).distinct().all()
    ]
    return paper_ids


def search_chunks(db: Session, paper_ids: list[int], query: str, top_k: int = 15) -> list[dict]:
    """Search relevant chunks across workspace papers."""
    if not paper_ids:
        return []

    chunks = (
        db.query(PaperChunk)
        .filter(PaperChunk.paper_id.in_(paper_ids))
        .all()
    )

    keywords = set(query.lower().split())
    scored = []
    for chunk in chunks:
        content_lower = chunk.content.lower()
        score = sum(1 for kw in keywords if kw in content_lower)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [c for _, c in scored[:top_k]]

    paper_cache = {}
    results = []
    for chunk in top_chunks:
        if chunk.paper_id not in paper_cache:
            paper = db.query(Paper).get(chunk.paper_id)
            paper_cache[chunk.paper_id] = paper.title if paper else "Unknown"
        results.append({
            "paper_id": chunk.paper_id,
            "paper_title": paper_cache[chunk.paper_id],
            "content": chunk.content,
            "page_num": chunk.page_num,
        })
    return results


def chat_answer(db: Session, session_id: int, user_message: str) -> tuple[str, list[int]]:
    """Generate a RAG-based answer for a chat message. Returns (answer, referenced_paper_ids)."""
    chat_session = db.query(ChatSession).get(session_id)
    if not chat_session:
        return "会话不存在", []

    paper_ids = get_workspace_paper_ids(db, chat_session.workspace_id)

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(6)
        .all()
    )
    history.reverse()

    relevant_chunks = search_chunks(db, paper_ids, user_message)

    context = ""
    referenced_ids = set()
    if relevant_chunks:
        context = "相关论文片段:\n\n"
        for chunk in relevant_chunks:
            context += f"【{chunk['paper_title']}】(p.{chunk['page_num'] or '?'})\n{chunk['content']}\n\n"
            referenced_ids.add(chunk["paper_id"])

    conversation = ""
    for msg in history:
        role_label = "用户" if msg.role == "user" else "助手"
        conversation += f"{role_label}: {msg.content}\n\n"

    prompt = f"{context}\n对话历史:\n{conversation}\n用户: {user_message}"

    answer = get_completion(
        prompt=prompt,
        system=CHAT_SYSTEM,
        max_tokens=2000,
        temperature=0.3,
    )

    return answer, list(referenced_ids)
