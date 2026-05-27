"""AI reading report generation service."""

from sqlalchemy.orm import Session

from paperader.llm.client import get_completion
from paperader.models.chunk import PaperChunk
from paperader.models.paper import Paper

REPORT_SYSTEM = """你是一个学术论文阅读助手。根据提供的论文信息和全文内容，生成一份结构化的阅读报告。
报告应使用中文，采用 Markdown 格式，包含以下部分：
1. **核心贡献** — 论文的主要贡献和创新点（2-3句）
2. **研究动机** — 论文解决什么问题，为什么重要
3. **方法概述** — 核心方法/框架的简要说明
4. **关键结果** — 主要实验结果和发现
5. **局限性与未来方向** — 论文的不足和可能的后续研究
6. **与相关工作的区别** — 和已有方法的核心差异

保持简洁专业，每部分不超过3-4句话。"""


def generate_report(db: Session, paper_id: int) -> str | None:
    """Generate an AI reading report for a paper using its chunks."""
    paper = db.query(Paper).get(paper_id)
    if not paper:
        return None

    chunks = (
        db.query(PaperChunk)
        .filter(PaperChunk.paper_id == paper_id)
        .order_by(PaperChunk.chunk_index)
        .all()
    )

    paper_context = f"标题: {paper.title}\n"
    if paper.authors:
        paper_context += f"作者: {', '.join(paper.authors[:5])}\n"
    if paper.venue:
        paper_context += f"会议/期刊: {paper.venue} {paper.year or ''}\n"
    if paper.abstract:
        paper_context += f"摘要: {paper.abstract}\n"

    if chunks:
        full_text = "\n\n".join(c.content for c in chunks[:40])
        max_chars = 24000
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "\n...[truncated]"
        paper_context += f"\n全文内容:\n{full_text}"
    elif paper.abstract:
        paper_context += "\n（无全文，仅基于摘要生成报告）"
    else:
        return None

    report = get_completion(
        prompt=paper_context,
        system=REPORT_SYSTEM,
        max_tokens=3000,
        temperature=0.3,
    )
    return report


FOLLOWUP_SYSTEM = """你是一个学术论文阅读助手。用户正在阅读一篇论文并提出问题。
根据论文内容回答用户的问题。如果论文内容中没有相关信息，请诚实说明。
使用中文回答，保持简洁专业。"""


def answer_paper_question(db: Session, paper_id: int, question: str) -> str | None:
    """Answer a follow-up question about a specific paper."""
    paper = db.query(Paper).get(paper_id)
    if not paper:
        return None

    chunks = (
        db.query(PaperChunk)
        .filter(PaperChunk.paper_id == paper_id)
        .order_by(PaperChunk.chunk_index)
        .all()
    )

    context = f"论文标题: {paper.title}\n"
    if paper.abstract:
        context += f"摘要: {paper.abstract}\n"

    if chunks:
        relevant = _find_relevant_chunks(chunks, question)
        context += "\n相关段落:\n" + "\n\n".join(c.content for c in relevant)

    prompt = f"{context}\n\n用户问题: {question}"
    return get_completion(
        prompt=prompt,
        system=FOLLOWUP_SYSTEM,
        max_tokens=2000,
        temperature=0.3,
    )


def _find_relevant_chunks(chunks: list[PaperChunk], query: str, top_k: int = 10) -> list[PaperChunk]:
    """Simple keyword relevance scoring for chunk retrieval."""
    keywords = set(query.lower().split())
    scored = []
    for chunk in chunks:
        content_lower = chunk.content.lower()
        score = sum(1 for kw in keywords if kw in content_lower)
        scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    result = [c for s, c in scored[:top_k] if s > 0]
    if not result:
        return chunks[:top_k]
    return result
