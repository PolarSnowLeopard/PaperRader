from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from paperader.models.paper import Paper
from paperader.services.report_service import answer_paper_question, generate_report
from server.deps import get_db

router = APIRouter(prefix="/api/papers", tags=["report"])


class ReportOut(BaseModel):
    paper_id: int
    content: str


class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    answer: str


@router.post("/{paper_id}/report", response_model=ReportOut)
def create_report(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    report = generate_report(db, paper_id)
    if report is None:
        raise HTTPException(status_code=400, detail="Cannot generate report: no content available")

    paper.report = report
    db.flush()
    return ReportOut(paper_id=paper_id, content=report)


@router.get("/{paper_id}/report", response_model=ReportOut)
def get_report(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    if not paper.report:
        raise HTTPException(status_code=404, detail="Report not generated yet")
    return ReportOut(paper_id=paper_id, content=paper.report)


@router.post("/{paper_id}/ask", response_model=QuestionResponse)
def ask_paper_question(paper_id: int, req: QuestionRequest, db: Session = Depends(get_db)):
    answer = answer_paper_question(db, paper_id, req.question)
    if answer is None:
        raise HTTPException(status_code=400, detail="Cannot answer: paper not found")
    return QuestionResponse(answer=answer)
