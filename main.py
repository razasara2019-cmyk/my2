"""
main.py – الحارس الصامت (AlSamit) مع TinyLlama عبر llama-server
الإصدار: 6.3 – خادم دائم، أسرع بكثير، بدون subprocess
"""

import os
import sys
import logging
import time
import random
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

import requests
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
# إعدادات خادم llama-server
# ============================================================

LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL", "http://127.0.0.1:8080")

# ردود احتياطية في حال فشل النموذج المحلي
FALLBACK_RESPONSES = [
    "أحتاج لحظة لأتأمل في هذا، ثم أجيبك.",
    "سؤالك مهم، ولكن الإجابة تحتاج إلى تركيز أعمق.",
    "تفكرت في الأمر، ويجب أن أبحث في دستوري أكثر.",
    "هذا محل تأمل، سأعود إليك بإجابة إن شاء الله.",
    "لا أملك علماً كافياً بهذا الشأن حالياً.",
    "سؤالك جميل، لكني بحاجة إلى وقت للتفكر فيه.",
]

# ردود سريعة للتحيات (بدون استدعاء النموذج)
QUICK_RESPONSES = {
    "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته.",
    "السلام": "وعليكم السلام.",
    "مرحبا": "مرحباً بك. كيف يمكنني مساعدتك؟",
    "مرحباً": "مرحباً بك.",
    "اهلا": "أهلاً بك.",
    "كيف حالك": "بخير، شكراً للسؤال. كيف يمكنني خدمتك؟",
    "شكرا": "عفواً، هذا من واجبي.",
    "جزاك الله خير": "وإياكم، آمين.",
}

# ============================================================
# دالة استدعاء TinyLlama عبر llama-server
# ============================================================

def is_llama_server_running() -> bool:
    """التحقق من أن خادم llama-server يعمل ويستجيب"""
    try:
        response = requests.get(f"{LLAMA_SERVER_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def call_tinyllama(prompt: str, max_tokens: int = 150) -> str:
    """استدعاء نموذج TinyLlama عبر خادم llama-server (أسرع بكثير)"""
    try:
        response = requests.post(
            f"{LLAMA_SERVER_URL}/completion",
            json={
                "prompt": prompt,
                "n_predict": max_tokens,
                "temperature": 0.5,
                "top_k": 20,
                "top_p": 0.85,
                "repeat_penalty": 1.1,
                "stop": ["</s>", "\n\n\n"]
            },
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", "")
            if content and len(content.strip()) > 0:
                return content.strip()
            else:
                logger.warning("⚠️ رد فارغ من llama-server")
                return random.choice(FALLBACK_RESPONSES)
        else:
            logger.error(f"❌ llama-server رد برمز خطأ: {response.status_code}")
            return random.choice(FALLBACK_RESPONSES)
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ llama-server غير متاح. هل هو مشغل؟")
        return "الخادم الداخلي غير متاح حالياً."
    except requests.exceptions.Timeout:
        logger.error("❌ llama-server تجاوز الوقت المسموح")
        return "النموذج يستغرق وقتاً طويلاً، حاول مجدداً."
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع في llama-server: {e}")
        return random.choice(FALLBACK_RESPONSES)

def get_quick_response(message: str) -> Optional[str]:
    """رد سريع للتحيات والكلمات المفتاحية (بدون استدعاء النموذج)"""
    msg_lower = message.lower().strip()
    
    # تطابق تام
    for key, response in QUICK_RESPONSES.items():
        if msg_lower == key.lower():
            return response
    
    # تطابق جزئي (إذا احتوى على كلمة التحية)
    for key, response in QUICK_RESPONSES.items():
        if key.lower() in msg_lower and len(key) > 2:
            return response
    
    return None

# ============================================================
# نماذج البيانات (Pydantic Models)
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
    logger.info("🛡️ الحارس الصامت v6.3 - مع خادم llama-server الدائم")
    logger.info("=" * 60)
    logger.info(f"   • الدستور: {'✅ محمول' if entity.quran.is_loaded else '❌ غير محمول'}")
    logger.info(f"   • خادم llama-server: {LLAMA_SERVER_URL}")
    logger.info("   • وضع التشغيل: محلي بالكامل (بدون إنترنت)")
    logger.info("=" * 60)
    
    # التحقق من اتصال llama-server
    if is_llama_server_running():
        logger.info("✅ llama-server متصل ويعمل")
    else:
        logger.warning(f"⚠️ لا يمكن الاتصال بـ llama-server على {LLAMA_SERVER_URL}")
        logger.info("💡 لتشغيل الخادم: cd ~/my2/llama.cpp/build/bin && ./llama-server -m ../../../models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf -t 2 -c 512 --mlock --host 127.0.0.1 --port 8080 -np 1")
    
    yield
    logger.info("🛡️ الحارس الصامت ينهي عمله")


# ============================================================
# تطبيق FastAPI
# ============================================================

app = FastAPI(
    title="الحارس الصامت",
    description="كيان دستوري حي، مستقل بالكامل، يعمل على TinyLlama عبر خادم دائم",
    version="6.3",
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
# نقاط النهاية الأساسية
# ============================================================

@app.get("/")
async def root(request: Request):
    """الصفحة الرئيسية"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """فحص صحة الخدمة"""
    llama_server_ok = is_llama_server_running()
    
    return {
        "status": "ok",
        "version": "6.3",
        "entity": entity.IDENTITY["name"],
        "quran_loaded": entity.quran.is_loaded,
        "llama_server_connected": llama_server_ok,
        "mode": "local"
    }


@app.get("/status")
async def get_status():
    """الحالة الكاملة للكيان"""
    return entity.get_full_state()


@app.get("/model/status")
async def model_status():
    """حالة خادم النموذج"""
    llama_server_ok = is_llama_server_running()
    
    return {
        "model": "TinyLlama-1.1B",
        "server_url": LLAMA_SERVER_URL,
        "server_available": llama_server_ok,
        "quantization": "Q4_K_M",
        "mode": "llama-server"
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
    return {"keyword": keyword, "count": len(results), "results": results, "status": "success"}


@app.get("/quran/random")
async def random_verse():
    """آية عشوائية للتأمل"""
    verse = entity.get_random_quran_verse()
    if verse:
        return verse
    return {"error": "القرآن غير محمول", "status": "error"}


# ============================================================
# نقطة المحادثة الرئيسية (مع ردود سريعة للتحيات)
# ============================================================

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """محادثة مع الحارس الصامت - يستخدم llama-server الدائم"""
    start_time = time.time()
    
    try:
        logger.info(f"📨 استلام طلب: {chat_request.message[:100]}...")
        
        if not chat_request.message or not chat_request.message.strip():
            raise HTTPException(status_code=400, detail="الرسالة فارغة")
        
        entity.record_interaction()
        
        # 1. محاولة الرد السريع (للتحيات)
        quick_response = get_quick_response(chat_request.message)
        if quick_response:
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"✅ رد سريع (بدون نموذج): {quick_response[:50]}...")
            return ChatResponse(
                response=quick_response,
                sources=[],
                status="success",
                processing_time_ms=round(processing_time, 2),
                model_used="quick_response"
            )
        
        # 2. بناء الرسالة للنموذج
        system_prompt = "أنت الحارس الصامت. القرآن هو دستورك. أجب باختصار وبحكمة (جملتين إلى 3 جمل كحد أقصى)."
        user_prompt = f"{system_prompt}\n\nسؤال المستخدم: {chat_request.message}\n\nالإجابة المختصرة:"
        
        # 3. استدعاء النموذج عبر llama-server
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
        logger.error(f"❌ خطأ غير متوقع في /chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# نقطة إضافة الأفكار (فحصها ضد الدستور)
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
    """اختبار اتصال llama-server والنموذج"""
    # اختبار الاتصال بالخادم
    server_ok = is_llama_server_running()
    
    if not server_ok:
        return {
            "status": "error",
            "server_available": False,
            "message": "llama-server غير متاح",
            "command": "cd ~/my2/llama.cpp/build/bin && ./llama-server -m ../../../models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf -t 2 -c 512 --mlock --host 127.0.0.1 --port 8080 -np 1"
        }
    
    # اختبار توليد رد
    test_response = call_tinyllama("قل مرحبا", max_tokens=20)
    
    return {
        "status": "ok" if test_response not in FALLBACK_RESPONSES else "warning",
        "server_available": True,
        "model": "TinyLlama-1.1B",
        "response": test_response,
        "server_url": LLAMA_SERVER_URL
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
    logger.info(f"🧠 خادم النموذج: {LLAMA_SERVER_URL}")
    logger.info("=" * 60)
    
    uvicorn.run("main:app", host=host, port=port, reload=False)
