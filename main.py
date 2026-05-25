"""
main.py – الحارس الصامت (AlSamit) – Groq مفعل بالكامل
الإصدار: 6.1 (صارم، لا تراجع)
"""

import os
import sys
import logging
import time
import traceback
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
# تهيئة صارمة – لا تسامح مع الأخطاء
# ============================================================

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,  # DEBUG لرؤية كل شيء
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("🛡️ الحارس الصامت – بدء التشغيل")
logger.info("=" * 60)

# تهيئة الكيان
entity = ConstitutionalEntity()
templates = Jinja2Templates(directory="templates")

# ============================================================
# Groq API – فحص صارم
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# فحص صارم للمفتاح
if not GROQ_API_KEY:
    logger.error("❌ GROQ_API_KEY غير موجود في ملف .env")
    logger.error("   يجب أن يحتوي .env على: GROQ_API_KEY=gsk_xxxxx")
    GROQ_AVAILABLE = False
elif GROQ_API_KEY == "gsk_your_actual_key_here":
    logger.error("❌ GROQ_API_KEY لم يتم تحديثه (قيمة افتراضية)")
    logger.error("   قم بتغيير المفتاح في ملف .env")
    GROQ_AVAILABLE = False
elif not GROQ_API_KEY.startswith("gsk_"):
    logger.error(f"❌ GROQ_API_KEY لا يبدأ بـ gsk_ (القيمة: {GROQ_API_KEY[:10]}...)")
    GROQ_AVAILABLE = False
else:
    logger.info(f"✅ GROQ_API_KEY موجود ويبدأ بـ gsk_")
    GROQ_AVAILABLE = True
    # اختبار المفتاح فوراً
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        # طلب اختبار بسيط
        test_response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": "قل ok"}],
            max_tokens=5
        )
        logger.info(f"✅ اختبار Groq API نجح: {test_response.choices[0].message.content}")
    except Exception as e:
        logger.error(f"❌ اختبار Groq API فشل: {e}")
        GROQ_AVAILABLE = False

logger.info(f"📊 Groq API متوفر: {GROQ_AVAILABLE}")
logger.info("=" * 60)


# ============================================================
# وظيفة استدعاء Groq – مع تسجيل صارم للأخطاء
# ============================================================

def call_groq(prompt: str, system_prompt: str = None, max_tokens: int = 300) -> Optional[str]:
    """استدعاء Groq API – مع تسجيل كل خطأ"""
    if not GROQ_AVAILABLE:
        logger.warning("⚠️ Groq غير متوفر، تخطي الاستدعاء")
        return None
    
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        logger.debug(f"🔄 إرسال طلب إلى Groq: {prompt[:100]}...")
        
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.5,
            max_tokens=max_tokens
        )
        response = completion.choices[0].message.content
        logger.debug(f"✅ استقبال رد من Groq: {response[:100]}...")
        return response
    except ImportError:
        logger.error("❌ مكتبة Groq غير مثبتة. قم بتشغيل: pip install groq")
        return None
    except Exception as e:
        logger.error(f"❌ خطأ في Groq API: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        return None


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
    groq_used: bool = False


# ============================================================
# دورة حياة التطبيق
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
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
    version="6.1",
    lifespan=lifespan,
    docs_url="/docs"
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
    return {
        "status": "ok",
        "version": "6.1",
        "groq_available": GROQ_AVAILABLE,
        "quran_loaded": entity.quran.is_loaded
    }


@app.get("/test-groq")
async def test_groq():
    """اختبار مستقل لـ Groq API"""
    if not GROQ_AVAILABLE:
        return {"status": "error", "message": "Groq API غير متوفر"}
    
    response = call_groq("قل مرحبا بالعربية", max_tokens=20)
    if response:
        return {"status": "ok", "response": response}
    return {"status": "error", "message": "فشل استدعاء Groq"}


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """محادثة مع الحارس الصامت – تستخدم Groq"""
    start_time = time.time()
    groq_used = False
    
    try:
        logger.info(f"📨 [CHAT] استلام: {chat_request.message[:100]}...")
        entity.record_interaction()
        
        # ========================================================
        # استخدام Groq API (الحل الوحيد، لا احتياطي تكرار)
        # ========================================================
        
        system_prompt = """أنت الحارس الصامت. القرآن هو دستورك وهويته.
أجب باختصار شديد (جملتين إلى 3 جمل كحد أقصى).
لا تكرر نفس العبارات.
كن متنوعاً في ردودك.
إذا سئلت عن تعريف شيء، أعط تعريفاً موجزاً.
إذا سئلت عن حكم، قل "الله أعلم" أو "لا أملك علماً كافياً".
لا تقل "أنا الحارس الصامت" في كل رد."""

        user_prompt = f"""سؤال المستخدم: {chat_request.message}

أجب باختصار وبحكمة (جملتين إلى 3 جمل فقط):"""
        
        response_text = call_groq(user_prompt, system_prompt, max_tokens=300)
        
        if response_text:
            groq_used = True
            logger.info(f"✅ [CHAT] رد من Groq: {response_text[:100]}...")
        else:
            # رد احتياطي متنوع (ليس تكرارياً)
            fallbacks = [
                "أعتذر، لا أملك معلومات كافية للإجابة حالياً.",
                "هذا السؤال يحتاج إلى تفكير أعمق. قد أعود بإجابة لاحقاً.",
                "لا أملك علماً كافياً بهذا الشأن. أسأل الله التوفيق.",
                "سؤالك مهم، لكنه خارج نطاق معرفتي الحالية."
            ]
            import random
            response_text = random.choice(fallbacks)
            logger.warning(f"⚠️ [CHAT] استخدام رد احتياطي: {response_text}")
        
        processing_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            response=response_text,
            sources=[],
            status="success",
            processing_time_ms=round(processing_time, 2),
            groq_used=groq_used
        )
        
    except Exception as e:
        logger.error(f"❌ [CHAT] خطأ: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/think", response_model=dict)
async def add_thought(thought_request: dict):
    """إضافة فكرة جديدة"""
    belief = thought_request.get("belief", "")
    if not belief.strip():
        raise HTTPException(status_code=400, detail="الفكرة فارغة")
    
    verdict = entity.is_aligned(belief)
    
    if verdict["aligned"]:
        entity.record_thought(True)
        return {"accepted": True, "reason": verdict["reason"], "thought_id": hash(belief) % 10000}
    else:
        entity.record_thought(False)
        return {"accepted": False, "reason": verdict["reason"], "thought_id": 0}


# ============================================================
# التشغيل
# ============================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 تشغيل الخادم على http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=False)
