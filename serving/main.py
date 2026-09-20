"""FastAPI app exposing the hybrid retrieval pipeline as a single
question-answering endpoint, per docs/PLAN.md's Phase 5.

Usage:
    .venv/bin/uvicorn serving.main:app --reload --port 8000

Then POST to /ask, or use the auto-generated docs at /docs.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from retrieval.pipeline import retrieve
from .generation import synthesize_answer

app = FastAPI(
    title="Telecom Network Digital Twin — Hybrid Graph + Vector RAG",
    description="Ask a question about the synthetic network topology or support tickets.",
    version="0.1.0",
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["what's causing the outage tickets near tower-032?"])
    top_k: int = Field(10, ge=1, le=50)


class AskResponse(BaseModel):
    question: str
    mode: str
    answer: str
    retrieval: dict


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        result = retrieve(request.question, top_k=request.top_k)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Retrieval failed: {exc}") from exc

    try:
        answer = synthesize_answer(request.question, result)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Answer synthesis failed: {exc}") from exc

    return AskResponse(question=request.question, mode=result["mode"], answer=answer, retrieval=result)
