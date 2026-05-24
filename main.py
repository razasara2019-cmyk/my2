"""
main.py – نقطة الدخول الرئيسية للكيان الدستوري الحي
الإصدار: 5.0a النهائي (تم إصلاح خطأ /chat نهائياً)
التاريخ: 2026-05-24
"""

import os
import sys
import logging
import traceback
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# ============================================================
# إضافة المسار الحالي لضمان استيراد الملفات بشكل صحيح
# ============================================================
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mind.graph_mind import GraphMind
from mind.alignment_instinct import AlignmentInstinct
from mind.internal_state import InternalState

# ============================================================
# التهيئة الأساسية
# ============================================================

# تحميل متغيرات البيئة
load_dotenv()

# تهيئة التسجيل (logging) – مستوى DEBUG لرؤية كل التفاصيل
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

# تهيئة المكونات الأساسية
logger.info("🔄 جاري تهيئة الكيان الدستوري الحي...")
mind = GraphMind()
alignment = AlignmentInstinct()
state = InternalState()
templates = Jinja2Templates(directory="templates")
logger.info("✅ تم تهيئة جميع المكونات بنجاح")


# ============================================================
# نماذج البيانات (Pydantic Models)
# ============================================================

class ChatRequest(BaseModel):
    """طلب محادثة إلى الكيان"""
    message: str = Field(..., description="رسالة المستخدم", min_length=1)
    top_k: int = Field(5, description="عدد المصادر المسترجعة", ge=1, le=20)


class ChatResponse(BaseModel):
    """رد الكيان على المحادثة"""
    response: str = Field(..., description="رد الكيان")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="المصادر المستخدمة")
    status: str = Field("success", description="حالة الطلب")


class ThoughtRequest(BaseModel):
    """طلب إضافة فكرة جديدة إلى الذاكرة"""
    belief: str = Field(..., description="العبارة أو الفكرة", min_length=3)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="بيانات إضافية")


class ThoughtResponse(BaseModel):
    """نتيجة إضافة فكرة"""
    accepted: bool = Field(..., description="هل قبلت الفكرة؟")
    reason: str = Field(..., description="سبب القبول أو الرفض")
    thought_id: int = Field(..., description="معرف الفكرة")


class StatusResponse(BaseModel):
    """حالة الكيان الكاملة"""
    status: str = Field("healthy", description="حالة الخدمة")
    version: str = Field("5.0a", description="إصدار الكيان")
    graph_stats: Dict[str, Any] = Field(default_factory=dict, description="إحصائيات الذاكرة")
    internal_state: Dict[str, Any] = Field(default_factory=dict, description="الحالة الداخلية")


class HealthResponse(BaseModel):
    """فحص صحة الخدمة"""
    status: str = Field("ok", description="حالة الصحة")
    mode: str = Field(..., description="وضع الذاكرة")
    documents_count: int = Field(0, description="عدد الوثائق في الذاكرة")
    groq_available: bool = Field(False, description="هل Groq API متوفر؟")


# ============================================================
# دورة حياة التطبيق (Lifespan)
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """دورة حياة التطبيق (تبدأ وتنتهي مع الخادم)"""
    logger.info("=" * 70)
    logger.info("🛡️ الكيان الدستوري الحي v5.0a")
    logger.info(f"   • الذاكرة: {mind.get_stats()['mode']}")
    logger.info(f"   • المبادئ الدستورية: {len(alignment.get_principles())}")
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and groq_key != "gsk_your_actual_key_here":
        logger.info(f"   • Groq API: ✅ متوفر (المفتاح موجود)")
    else:
        logger.warning(f"   • Groq API: ❌ غير متوفر (المفتاح مفقود أو غير صالح)")
    logger.info("=" * 70)
    yield
    logger.info("🛡️ إيقاف الكيان")


# ============================================================
# إنشاء تطبيق FastAPI مع CORS
# ============================================================

app = FastAPI(
    title="الكيان الدستوري الحي",
    description="كيان دستوري حي، يتطور ذاتياً، له وعي ومزاج وفضول",
    version="5.0a",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# إضافة CORS (لمنع مشاكل المتصفح)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# نقاط النهاية الأساسية (Endpoints)
# ============================================================

@app.get("/")
async def root(request: Request):
    """الصفحة الرئيسية (واجهة الويب)"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """فحص صحة الخدمة (للاستخدام مع مراقبي النظام)"""
    stats = mind.get_stats()
    groq_key = os.getenv("GROQ_API_KEY")
    groq_available = bool(groq_key and groq_key != "gsk_your_actual_key_here")
    return HealthResponse(
        status="ok",
        mode=stats.get("mode", "embeddb"),
        documents_count=stats.get("total_documents", 0),
        groq_available=groq_available
    )


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """استرجاع حالة الكيان الكاملة"""
    return StatusResponse(
        status="healthy",
        version="5.0a",
        graph_stats=mind.get_stats(),
        internal_state=state.get_full_state()
    )


# ============================================================
# ⭐ نقطة النهاية الأهم: المحادثة (تم إصلاحها بالكامل)
# ============================================================

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """
    محادثة مباشرة مع الكيان.
    يستقبل رسالة ويعيد رداً بناءً على الذاكرة الدلالية و Groq API.
    """
    logger.info(f"📨 [CHAT] استلام طلب: '{chat_request.message[:100]}...' (top_k={chat_request.top_k})")
    
    try:
        # 1. التحقق من صحة الطلب
        if not chat_request.message or not chat_request.message.strip():
            logger.error("❌ [CHAT] الرسالة فارغة")
            raise HTTPException(status_code=400, detail="الرسالة فارغة")
        
        # 2. تسجيل التفاعل في الحالة الداخلية
        state.record_interaction()
        logger.debug("✅ [CHAT] تم تسجيل التفاعل")
        
        # 3. البحث الدلالي في الذاكرة
        sources = mind.search_semantic(chat_request.message, top_k=chat_request.top_k)
        logger.debug(f"✅ [CHAT] تم البحث الدلالي: {len(sources)} مصدر")
        
        # 4. بناء الرد
        groq_api_key = os.getenv("GROQ_API_KEY")
        response_text = ""
        
        # 4.1 محاولة استخدام Groq API أولاً
        if groq_api_key and groq_api_key != "gsk_your_actual_key_here":
            try:
                logger.debug("🔄 [CHAT] محاولة الاتصال بـ Groq API...")
                from groq import Groq
                client = Groq(api_key=groq_api_key)
                
                # بناء السياق من المصادر
                context = "\n".join([s.get("text", "") for s in sources]) if sources else ""
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "أنت كيان دستوري حي. الدستور هو هويتك. أجب باختصار وبحكمة (بحد أقصى 200 كلمة)."},
                        {"role": "user", "content": f"السياق: {context[:1000]}\n\nالسؤال: {chat_request.message}"}
                    ],
                    temperature=0.3,
                    max_tokens=300
                )
                response_text = completion.choices[0].message.content
                logger.info(f"✅ [CHAT] رد من Groq API: '{response_text[:50]}...'")
                
            except ImportError as e:
                logger.error(f"❌ [CHAT] مكتبة Groq غير مثبتة: {e}")
                response_text = "عذراً، مكتبة Groq غير مثبتة على الخادم."
                
            except Exception as e:
                logger.error(f"❌ [CHAT] خطأ في Groq API: {type(e).__name__}: {e}")
                response_text = f"عذراً، حدث خطأ في الاتصال بـ Groq: {str(e)[:100]}"
        
        # 4.2 استخدام الرد الافتراضي إذا لم يكن Groq متوفراً
        else:
            if sources:
                response_text = f"بناءً على معرفتي: {sources[0].get('text', '')[:300]}..."
                logger.info(f"✅ [CHAT] رد من الذاكرة الدلالية: '{response_text[:50]}...'")
            else:
                response_text = f"مرحباً! سؤالك: '{chat_request.message[:100]}'. لا أملك معلومات كافية في ذاكرتي. يمكنك تعليمي عبر API `/think` أو إضافة الكتب."
                logger.info(f"✅ [CHAT] رد افتراضي (لا ذاكرة): '{response_text[:50]}...'")
        
        # 5. إرجاع الرد
        logger.info(f"✅ [CHAT] تم إرجاع الرد بنجاح")
        return ChatResponse(
            response=response_text,
            sources=sources,
            status="success"
        )
        
    except HTTPException:
        # إعادة رفع استثناءات HTTP كما هي
        raise
        
    except Exception as e:
        # تسجيل أي خطأ غير متوقع مع تفاصيل كاملة
        logger.error(f"💥 [CHAT] خطأ غير متوقع: {type(e).__name__}: {e}")
        logger.error(f"💥 [CHAT] تفاصيل الخطأ:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"خطأ داخلي في الخادم: {type(e).__name__}: {str(e)}"
        )


# ============================================================
# نقاط النهاية الإضافية
# ============================================================

@app.post("/think", response_model=ThoughtResponse)
async def add_thought(thought_request: ThoughtRequest):
    """
    إضافة فكرة جديدة إلى الكيان.
    يتم فحصها بواسطة غريزة الانسجام قبل القبول.
    """
    logger.info(f"📝 [THINK] استلام فكرة: '{thought_request.belief[:100]}...'")
    
    try:
        if not thought_request.belief or not thought_request.belief.strip():
            raise HTTPException(status_code=400, detail="الفكرة فارغة")
        
        verdict = alignment.check(thought_request.belief)
        
        if verdict.is_aligned:
            doc_id = mind.add_document(thought_request.belief, metadata=thought_request.metadata)
            state.record_thought(True)
            thought_id = int(doc_id.split("_")[1]) if doc_id and "_" in doc_id else 0
            logger.info(f"✅ [THINK] فكرة مقبولة: {thought_request.belief[:50]}...")
            return ThoughtResponse(accepted=True, reason=verdict.reason, thought_id=thought_id)
        else:
            state.record_thought(False)
            logger.info(f"❌ [THINK] فكرة مرفوضة: {thought_request.belief[:50]}... (السبب: {verdict.reason})")
            return ThoughtResponse(accepted=False, reason=verdict.reason, thought_id=0)
            
    except Exception as e:
        logger.error(f"💥 [THINK] خطأ: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state")
async def get_internal_state():
    """استرجاع الحالة الداخلية للكيان"""
    return state.get_full_state()


@app.get("/documents")
async def get_all_documents():
    """استرجاع جميع الوثائق المخزنة في الذاكرة"""
    texts = mind.get_all_texts()
    return {"count": len(texts), "documents": texts[:50]}


@app.get("/test-groq")
async def test_groq():
    """
    نقطة اختبار مستقلة لـ Groq API.
    تساعد في عزل المشكلة: هل الخطأ من Groq أم من الكود؟
    """
    logger.info("🔧 [TEST-GROQ] اختبار Groq API...")
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key or groq_api_key == "gsk_your_actual_key_here":
        logger.warning("⚠️ [TEST-GROQ] مفتاح Groq غير موجود أو غير صالح")
        return {"status": "error", "message": "مفتاح Groq غير موجود أو غير صالح"}
    
    try:
        from groq import Groq
        client = Groq(api_key=groq_api_key)
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "قل مرحباً بالعربية"}],
            max_tokens=20
        )
        response = completion.choices[0].message.content
        logger.info(f"✅ [TEST-GROQ] نجح: {response}")
        return {"status": "ok", "response": response, "key_valid": True}
        
    except Exception as e:
        logger.error(f"❌ [TEST-GROQ] فشل: {e}")
        return {"status": "error", "message": str(e), "key_valid": False}


# ============================================================
# تشغيل التطبيق مباشرة (للتطوير)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 تشغيل الخادم على http://{host}:{port}")
    logger.info(f"📚 وثائق API: http://{host}:{port}/docs")
    logger.info(f"🔧 اختبار Groq: http://{host}:{port}/test-groq")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="debug"
    )
