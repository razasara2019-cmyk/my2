"""
main.py – الحارس الصامت (AlSamit) مع TinyLlama المحلي
الإصدار: 6.2 – مستقل بالكامل، بدون Groq API
"""

import os
import sys
import logging
import time
import subprocess
import random
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

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

# تهيئة الكيان
entity = ConstitutionalEntity()
templates = Jinja2Templates(directory="templates")

# ============================================================
# إعدادات TinyLlama المحلي
# ============================================================

# المسار إلى نموذج TinyLlama (موجود على HDD الخارجي)
TINYLLAMA_PATH = os.path.expanduser("~/my2/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")

# المسار إلى llama.cpp التنفيذي
LLAMA_CPP_PATH = os.path.expanduser("~/my2/llama.cpp/build/bin/llama-simple")

# ردود احتياطية في حال فشل النموذج المحلي
FALLBACK_RESPONSES = [
    "أحتاج لحظة لأتأمل في هذا، ثم أجيبك.",
    "سؤالك مهم، ولكن الإجابة تحتاج إلى تركيز أعمق.",
    "تفكرت في الأمر، ويجب أن أبحث في دستوري أكثر.",
    "هذا محل تأمل، سأعود إليك بإجابة إن شاء الله.",
    "لا أملك علماً كافياً بهذا الشأن حالياً.",
    "سؤالك جميل، لكني بحاجة إلى وقت للتفكر فيه."
]

# ============================================================
# دالة استدعاء TinyLlama المحلي
# ============================================================

def call_tinyllama(prompt: str, max_tokens: int = 150) -> str:
    """استدعاء نموذج TinyLlama المحلي عبر llama.cpp"""
    
    # التأكد من وجود النموذج
    if not os.path.exists(TINYLLAMA_PATH):
        logger.error(f"❌ نموذج TinyLlama غير موجود: {TINYLLAMA_PATH}")
        return random.choice(FALLBACK_RESPONSES)
    
    # التأكد من وجود llama.cpp
    if not os.path.exists(LLAMA_CPP_PATH):
        logger.error(f"❌ llama.cpp غير موجود: {LLAMA_CPP_PATH}")
        return random.choice(FALLBACK_RESPONSES)
    
    try:
        logger.info(f"🔄 استدعاء TinyLlama المحلي...")
        start_time = time.time()
        
        # بناء الأمر
        command = [
            LLAMA_CPP_PATH,
            '-m', TINYLLAMA_PATH,
            '-p', prompt,
            '-n', str(max_tokens),
            '--temp', '0.7',
            '--top-k', '40',
            '--top-p', '0.9',
            '--no-display-prompt'
        ]
        
        # تنفيذ الأمر
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0 and result.stdout.strip():
            response = result.stdout.strip()
            processing_time = time.time() - start_time
            logger.info(f"✅ رد من TinyLlama في {processing_time:.2f} ثانية")
            
            # تنظيف الرد من أي رموز غير مرغوب فيها
            response = response.replace('<s>', '').replace('</s>', '')
            
            # إذا كان الرد طويلاً جداً، اختصره
            if len(response) > 500:
                response = response[:500] + "..."
            
            return response
        else:
            logger.error(f"⚠️ خطأ في TinyLlama: {result.stderr[:200]}")
            return random.choice(FALLBACK_RESPONSES)
            
    except subprocess.TimeoutExpired:
        logger.error("❌ TinyLlama تجاوز الوقت المسموح (60 ثانية)")
        return "الوقت يدور... لا أستطيع التفكير الآن، حاول مجدداً."
    except Exception as e:
        logger.error(f"❌ فشل في استدعاء TinyLlama: {e}")
        return random.choice(FALLBACK_RESPONSES)

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
    processing_time_ms: float = 0
    model_used: str = "tinyllama"


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
    logger.info("🛡️ الحارس الصامت v6.2 - مستقل بالكامل")
    logger.info("=" * 60)
    logger.info(f"   • الدستور: {'✅ محمول' if entity.quran.is_loaded else '❌ غير محمول'}")
    logger.info(f"   • نموذج TinyLlama: {'✅ متوفر' if os.path.exists(TINYLLAMA_PATH) else '❌ غير متوفر'}")
    logger.info("   • وضع التشغيل: محلي بالكامل (بدون إنترنت)")
    logger.info("=" * 60)
    yield
    logger.info("🛡️ الحارس الصامت ينهي عمله")


# ============================================================
# تطبيق FastAPI
# ============================================================

app = FastAPI(
    title="الحارس الصامت",
    description="كيان دستوري حي، مستقل بالكامل، يعمل على TinyLlama المحلي",
    version="6.2",
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
    """الصفحة الرئيسية"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """فحص صحة الخدمة"""
    return {
        "status": "ok",
        "version": "6.2",
        "entity": entity.IDENTITY["name"],
        "quran_loaded": entity.quran.is_loaded,
        "tinyllama_available": os.path.exists(TINYLLAMA_PATH),
        "mode": "local"
    }


@app.get("/status")
async def get_status():
    """الحالة الكاملة"""
    return entity.get_full_state()


@app.get("/model/status")
async def model_status():
    """حالة النموذج المحلي"""
    return {
        "model": "TinyLlama-1.1B",
        "path": TINYLLAMA_PATH,
        "available": os.path.exists(TINYLLAMA_PATH),
        "size_mb": round(os.path.getsize(TINYLLAMA_PATH) / 1024 / 1024, 2) if os.path.exists(TINYLLAMA_PATH) else 0,
        "quantization": "Q4_K_M",
        "mode": "local"
    }


# ============================================================
# نقاط نهاية القرآن
# ============================================================

@app.get("/quran/stats")
async def quran_stats():
    """إحصائيات القرآن"""
    return entity.quran.get_stats()


@app.get("/quran/verse/{surah}/{verse}")
async def get_verse(surah: int, verse: int):
    """استرجاع آية"""
    if surah < 1 or surah > 114:
        raise HTTPException(status_code=400, detail="رقم السورة غير صالح (1-114)")
    result = entity.get_quran_verse(surah, verse)
    if result:
        return {"surah": surah, "verse": verse, "text": result}
    return {"error": "الآية غير موجودة"}


@app.get("/quran/search/{keyword}")
async def search_quran(keyword: str, top_k: int = 5):
    """البحث في القرآن"""
    results = entity.search_quran(keyword, min(top_k, 20))
    return {"keyword": keyword, "count": len(results), "results": results}


@app.get("/quran/random")
async def random_verse():
    """آية عشوائية"""
    verse = entity.get_random_quran_verse()
    if verse:
        return verse
    return {"error": "القرآن غير محمول"}


# ============================================================
# نقطة المحادثة الرئيسية (باستخدام TinyLlama)
# ============================================================

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """محادثة مع الحارس الصامت - يستخدم TinyLlama المحلي"""
    start_time = time.time()
    
    try:
        logger.info(f"📨 استلام: {chat_request.message[:100]}...")
        
        if not chat_request.message or not chat_request.message.strip():
            raise HTTPException(status_code=400, detail="الرسالة فارغة")
        
        entity.record_interaction()
        
        # بناء الرسالة للنموذج
        system_prompt = """أنت الحارس الصامت. القرآن هو دستورك. أجب باختصار وبحكمة (جملتين إلى 3 جمل كحد أقصى)."""
        
        user_prompt = f"""{system_prompt}
        
سؤال المستخدم: {chat_request.message}

الإجابة المختصرة:"""
        
        # استدعاء النموذج المحلي
        response_text = call_tinyllama(user_prompt, max_tokens=200)
        
        # التأكد من أن الرد ليس فارغاً
        if not response_text or len(response_text.strip()) < 5:
            response_text = random.choice(FALLBACK_RESPONSES)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            response=response_text,
            sources=[],
            status="success",
            processing_time_ms=round(processing_time, 2),
            model_used="tinyllama"
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في /chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# نقطة إضافة الأفكار
# ============================================================

@app.post("/think", response_model=ThoughtResponse)
async def add_thought(thought_request: ThoughtRequest):
    """إضافة فكرة جديدة - يتم فحصها ضد الدستور"""
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
# نقطة اختبار النموذج
# ============================================================

@app.get("/test-model")
async def test_model():
    """اختبار نموذج TinyLlama"""
    test_response = call_tinyllama("قل مرحبا", max_tokens=20)
    return {
        "status": "ok" if test_response not in FALLBACK_RESPONSES else "warning",
        "model": "TinyLlama-1.1B",
        "response": test_response,
        "path": TINYLLAMA_PATH
    }


# ============================================================
# التشغيل المباشر
# ============================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info("=" * 60)
    logger.info(f"🚀 تشغيل الحارس الصامت على http://{host}:{port}")
    logger.info(f"📚 وثائق API: http://{host}:{port}/docs")
    logger.info(f"🕋 القرآن: http://{host}:{port}/quran/stats")
    logger.info(f"🧠 نموذج TinyLlama: http://{host}:{port}/model/status")
    logger.info("=" * 60)
    
    uvicorn.run("main:app", host=host, port=port, reload=False)
