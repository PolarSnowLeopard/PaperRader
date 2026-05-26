from dataclasses import dataclass

from paperader.llm.client import get_json_completion
from paperader.llm.prompts import RERANK_SYSTEM, RERANK_USER_TEMPLATE
from paperader.models.paper import Paper
from paperader.search.intent import SearchIntent


@dataclass
class RankedPaper:
    paper: Paper
    score: float
    reason: str


def rerank_papers(
    papers: list[Paper], intent: SearchIntent, top_k: int = 10
) -> list[RankedPaper]:
    if not papers:
        return []

    # Build paper text for LLM (batch up to 30 papers to stay within token limits)
    batch = papers[:30]
    papers_text = _format_papers(batch)

    prompt = RERANK_USER_TEMPLATE.format(
        intent_summary=intent.intent_summary,
        topics=", ".join(intent.topics),
        papers_text=papers_text,
    )

    result = get_json_completion(prompt=prompt, system=RERANK_SYSTEM, max_tokens=3000)

    # Handle both wrapped and unwrapped array
    if isinstance(result, dict):
        result = result.get("results", result.get("papers", []))

    ranked = []
    for item in result:
        idx = item.get("index", -1)
        if 0 <= idx < len(batch):
            ranked.append(
                RankedPaper(
                    paper=batch[idx],
                    score=float(item.get("score", 0)),
                    reason=item.get("reason", ""),
                )
            )

    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked[:top_k]


def _format_papers(papers: list[Paper]) -> str:
    lines = []
    for i, p in enumerate(papers):
        abstract_preview = ""
        if p.abstract:
            abstract_preview = p.abstract[:200] + ("..." if len(p.abstract) > 200 else "")
        lines.append(
            f"[{i}] {p.title}\n"
            f"    Authors: {', '.join(p.authors[:3]) if p.authors else 'N/A'}\n"
            f"    Year: {p.year or 'N/A'} | Venue: {p.venue or 'N/A'}\n"
            f"    Abstract: {abstract_preview}"
        )
    return "\n\n".join(lines)
