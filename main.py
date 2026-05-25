"""
main.py – نقطة الدخول الرئيسية للكيان الدستوري الحي
الإصدار: 5.0a النهائي
"""

import os
import logging
import traceback
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from mind.graph_mind import GraphMind
from mind.alignment_instinct import AlignmentInstinct
from mind.internal_state import InternalState

# ============================================================
# التهيئة الأساسية
# ============================================================

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

# تهيئة المكونات
mind = GraphMind()
alignment = AlignmentInstinct()
state = InternalState()
templates = Jinja2Templates(directory="templates")


# ============================================================
# نماذج البيانات
# ============================================================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)


class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    status: str


class ThoughtRequest(BaseModel):
    belief: str = Field(..., min_length=3)
    metadata: Optional[Dict[str, Any]] = None


class ThoughtResponse(BaseModel):
    accepted: bool
    reason: str
    thought_id: int


# ============================================================
# دورة حياة التطبيق
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("🛡️ الكيان الدستوري الحي v5.0a")
    logger.info(f"   • الذاكرة: {mind.get_stats()['mode']}")
    logger.info(f"   • المبادئ الدستورية: {len(alignment.get_principles())}")
    groq_key = os.getenv("GROQ_API_KEY")
    logger.info(f"   • Groq API: {'✅ متوفر' if groq_key else '❌ غير متوفر'}")
    logger.info("=" * 60)
    yield
    logger.info("🛡️ إيقاف الكيان")


# ============================================================
# تطبيق FastAPI
# ============================================================

app = FastAPI(
    title="الكيان الدستوري الحي",
    version="5.0a",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# نقاط النهاية
# ============================================================

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    stats = mind.get_stats()
    groq_key = os.getenv("GROQ_API_KEY")
    return {
        "status": "ok",
        "mode": stats.get("mode", "fastembed"),
        "documents_count": stats.get("total_documents", 0),
        "groq_available": bool(groq_key)
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
    try:
        logger.info(f"📨 استلام: {chat_request.message[:50]}...")
        
        if not chat_request.message or not chat_request.message.strip():
            raise HTTPException(status_code=400, detail="الرسالة فارغة")
        
        state.record_interaction()
        sources = mind.search_semantic(chat_request.message, top_k=chat_request.top_k)
        
        # رد بسيط (بدون Groq في البداية)
        if sources:
            response = f"بناءً على معرفتي: {sources[0]['text'][:200]}..."
        else:
            response = f"مرحباً! سؤالك: '{chat_request.message[:100]}'. لا أملك معلومات كافية في ذاكرتي."
        
        return ChatResponse(response=response, sources=sources, status="success")
        
    except Exception as e:
        logger.error(f"خطأ: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/think", response_model=ThoughtResponse)
async def add_thought(thought_request: ThoughtRequest):
    if not thought_request.belief or not thought_request.belief.strip():
        raise HTTPException(status_code=400, detail="الفكرة فارغة")
    
    verdict = alignment.check(thought_request.belief)
    
    if verdict.is_aligned:
        doc_id = mind.add_document(thought_request.belief, metadata=thought_request.metadata)
        state.record_thought(True)
        thought_id = int(doc_id.split("_")[1]) if doc_id and "_" in doc_id else 0
        return ThoughtResponse(accepted=True, reason=verdict.reason, thought_id=thought_id)
    else:
        state.record_thought(False)
        return ThoughtResponse(accepted=False, reason=verdict.reason, thought_id=0)


@app.get("/state")
async def get_internal_state():
    return state.get_full_state()


@app.get("/documents")
async def get_all_documents():
    texts = mind.get_all_texts()
    return {"count": len(texts), "documents": texts[:50]}


@app.get("/test-groq")
async def test_groq():
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key or groq_key == "gsk_your_actual_key_here":
        return {"status": "error", "message": "مفتاح Groq غير موجود"}
    
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "قل مرحباً"}],
            max_tokens=10
        )
        return {"status": "ok", "response": completion.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
