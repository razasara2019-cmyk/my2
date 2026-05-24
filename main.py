"""
main.py – نقطة الدخول الرئيسية للكيان الدستوري الحي
الإصدار: 5.0a النهائي
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from mind.graph_mind import GraphMind
from mind.alignment_instinct import AlignmentInstinct
from mind.internal_state import InternalState

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

mind = GraphMind()
alignment = AlignmentInstinct()
state = InternalState()
templates = Jinja2Templates(directory="templates")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)


class ChatResponse(BaseModel):
    response: str
    sources: list
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("🛡️ الكيان الدستوري الحي v5.0a")
    logger.info(f"   • الذاكرة: {mind.get_stats()['mode']}")
    logger.info(f"   • المبادئ الدستورية: {len(alignment.get_principles())}")
    logger.info("=" * 60)
    yield
    logger.info("🛡️ إيقاف الكيان")


app = FastAPI(
    title="الكيان الدستوري الحي",
    version="5.0a",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    stats = mind.get_stats()
    return {
        "status": "ok",
        "mode": stats.get("mode", "embeddb"),
        "documents_count": stats.get("total_documents", 0)
    }


@app.get("/status")
async def get_status():
    return {
        "status": "healthy",
        "version": "5.0a",
        "graph_stats": mind.get_stats(),
        "internal_state": state.get_full_state()
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    if not chat_request.message or not chat_request.message.strip():
        raise HTTPException(status_code=400, detail="الرسالة فارغة")
    
    state.record_interaction()
    sources = mind.search_semantic(chat_request.message, top_k=chat_request.top_k)
    
    if sources:
        response = f"بناءً على معرفتي: {sources[0]['text'][:300]}..."
    else:
        response = "لا أملك معلومات كافية للإجابة على هذا السؤال."
    
    return ChatResponse(response=response, sources=sources, status="success")


@app.get("/state")
async def get_internal_state():
    return state.get_full_state()


@app.get("/documents")
async def get_all_documents():
    texts = mind.get_all_texts()
    return {"count": len(texts), "documents": texts[:50]}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
