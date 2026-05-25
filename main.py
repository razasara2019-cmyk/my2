"""
main.py – واجهة الحارس الصامت
الإصدار: 6.0
"""

import os
import sys
import logging
import traceback
import time
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mind.entity import ConstitutionalEntity

# ============================================================
# التهيئة الأساسية
# ============================================================

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

# تهيئة الحارس الصامت
logger.info("=" * 60)
logger.info("🛡️ جاري تهيئة الحارس الصامت...")
logger.info("=" * 60)

entity = ConstitutionalEntity()
templates = Jinja2Templates(directory="templates")

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_AVAILABLE = bool(GROQ_API_KEY and GROQ_API_KEY != "gsk_your_actual_key_here")

if GROQ_AVAILABLE:
    logger.info(f"✅ Groq API متوفر")
else:
    logger.warning("⚠️ Groq API غير متوفر")

logger.info("=" * 60)
logger.info("✅ الحارس الصامت جاهز")
logger.info("=" * 60)


# ============================================================
# نماذج البيانات
# ============================================================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="رسالة المستخدم")
    top_k: int = Field(5, ge=1, le=20, description="عدد المصادر المسترجعة")


class ChatResponse(BaseModel):
    response: str = Field(..., description="رد الكيان")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="المصادر المستخدمة")
    status: str = Field("success", description="حالة الطلب")
    processing_time_ms: float = Field(0, description="وقت المعالجة بالميلي ثانية")


class ThoughtRequest(BaseModel):
    belief: str = Field(..., min_length=3, description="العبارة أو الفكرة")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="بيانات إضافية")


class ThoughtResponse(BaseModel):
    accepted: bool = Field(..., description="هل قبلت الفكرة؟")
    reason: str = Field(..., description="سبب القبول أو الرفض")
    thought_id: int = Field(..., description="معرف الفكرة")


# ============================================================
# دورة حياة التطبيق
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """دورة حياة التطبيق – تبدأ وتنتهي مع الخادم"""
    logger.info("🛡️ الحارس الصامت يبدأ عمله")
    logger.info(f"   • الدستور: {'✅ محمول' if entity.quran.is_loaded else '❌ غير محمول'}")
    logger.info(f"   • Groq: {'✅ متوفر' if GROQ_AVAILABLE else '❌ غير متوفر'}")
    yield
    logger.info("🛡️ الحارس الصامت ينهي عمله")


# ============================================================
# تطبيق FastAPI
# ============================================================

app = FastAPI(
    title="الحارس الصامت",
    description="كيان دستوري حي، يحرس القرآن في صمت",
    version="6.0",
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
    """الصفحة الرئيسية (واجهة الويب)"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """فحص صحة الخدمة"""
    return {
        "status": "ok",
        "version": "6.0",
        "entity": entity.IDENTITY["name"],
        "quran_loaded": entity.quran.is_loaded,
        "groq_available": GROQ_AVAILABLE
    }


@app.get("/status")
async def get_status():
    """الحالة الكاملة للحارس الصامت"""
    return entity.get_full_state()


@app.get("/quran/stats")
async def quran_stats():
    """إحصائيات الدستور القرآني"""
    return entity.quran.get_stats()


@app.get("/quran/verse/{surah}/{verse}")
async def get_verse(surah: int, verse: int):
    """استرجاع آية محددة"""
    if surah < 1 or surah > 114:
        raise HTTPException(status_code=400, detail="رقم السورة غير صالح (1-114)")
    if verse < 1:
        raise HTTPException(status_code=400, detail="رقم الآية غير صالح")
    
    result = entity.get_quran_verse(surah, verse)
    if result:
        return {"surah": surah, "verse": verse, "text": result, "status": "success"}
    return {"error": "الآية غير موجودة", "status": "error"}


@app.get("/quran/search/{keyword}")
async def search_quran(keyword: str, top_k: int = 5):
    """البحث في القرآن الكريم"""
    if not keyword or not keyword.strip():
        raise HTTPException(status_code=400, detail="كلمة البحث مطلوبة")
    
    results = entity.search_quran(keyword, min(top_k, 20))
    return {
        "keyword": keyword, 
        "count": len(results), 
        "results": results,
        "status": "success"
    }


@app.get("/quran/random")
async def random_verse():
    """آية عشوائية للتأمل"""
    verse = entity.get_random_quran_verse()
    if verse:
        return {"verse": verse, "status": "success"}
    return {"error": "القرآن غير محمول", "status": "error"}


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """محادثة مع الحارس الصامت"""
    start_time = time.time()
    
    try:
        logger.info(f"📨 استلام: {chat_request.message[:50]}...")
        
        if not chat_request.message or not chat_request.message.strip():
            raise HTTPException(status_code=400, detail="الرسالة فارغة")
        
        entity.record_interaction()
        
        # الرد الأساسي (سيتم تطويره لاحقاً)
        response = f"مرحباً! سؤالك: '{chat_request.message[:100]}'.\n\n"
        response += "أنا الحارس الصامت. أحرس القرآن في صمت. لا أنطق به، بل أعيشه."
        
        processing_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            response=response,
            sources=[],
            status="success",
            processing_time_ms=round(processing_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في /chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/think", response_model=ThoughtResponse)
async def add_thought(thought_request: ThoughtRequest):
    """إضافة فكرة جديدة – يتم فحصها ضد الدستور"""
    if not thought_request.belief or not thought_request.belief.strip():
        raise HTTPException(status_code=400, detail="الفكرة فارغة")
    
    verdict = entity.is_aligned(thought_request.belief)
    
    if verdict["aligned"]:
        entity.record_thought(True)
        thought_id = abs(hash(thought_request.belief)) % 10000
        logger.info(f"✅ فكرة مقبولة: {thought_request.belief[:50]}...")
        return ThoughtResponse(accepted=True, reason=verdict["reason"], thought_id=thought_id)
    else:
        entity.record_thought(False)
        for principle in verdict.get("conflicts", []):
            entity.record_contradiction(principle)
        logger.info(f"❌ فكرة مرفوضة: {thought_request.belief[:50]}...")
        return ThoughtResponse(accepted=False, reason=verdict["reason"], thought_id=0)


# ============================================================
# التشغيل المباشر
# ============================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info("=" * 60)
    logger.info(f"🚀 تشغيل الخادم على http://{host}:{port}")
    logger.info(f"📚 وثائق API: http://{host}:{port}/docs")
    logger.info(f"🕋 القرآن: http://{host}:{port}/quran/stats")
    logger.info("=" * 60)
    
    uvicorn.run("main:app", host=host, port=port, reload=False)
