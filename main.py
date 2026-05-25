"""
main.py – نقطة الدخول الرئيسية للكيان الدستوري الحي
الإصدار: 5.0a النهائي (تم إصلاح خطأ /chat وإضافة logging متقدم)
التاريخ: 2026-05-25
"""

# ============================================================
# المكتبات الأساسية (Standard Libraries)
# ============================================================
import os
import sys
import logging
import traceback
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

# ============================================================
# المكتبات الخارجية (Third-party Libraries)
# ============================================================
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

# ============================================================
# استيراد مكونات الكيان الداخلي
# ============================================================
from mind.graph_mind import GraphMind
from mind.alignment_instinct import AlignmentInstinct
from mind.internal_state import InternalState

# ============================================================
# تحميل متغيرات البيئة
# ============================================================
load_dotenv()

# ============================================================
# تهيئة نظام التسجيل (Logging) – مستوى DEBUG لرؤية كل التفاصيل
# ============================================================
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# تهيئة المكونات الأساسية للكيان
# ============================================================
logger.info("🔄 جاري تهيئة الكيان الدستوري الحي...")
logger.info("⏳ تهيئة الذاكرة الدلالية (GraphMind)...")
mind = GraphMind()
logger.info("✅ GraphMind جاهز")

logger.info("⏳ تهيئة غريزة الانسجام (AlignmentInstinct)...")
alignment = AlignmentInstinct()
logger.info(f"✅ AlignmentInstinct جاهز مع {len(alignment.get_principles())} مبدأ")

logger.info("⏳ تهيئة الحالة الداخلية (InternalState)...")
state = InternalState()
logger.info("✅ InternalState جاهز")

logger.info("⏳ تهيئة قوالب الواجهة (Templates)...")
templates = Jinja2Templates(directory="templates")
logger.info("✅ Templates جاهزة")

logger.info("✅ تم تهيئة جميع المكونات بنجاح")

# ============================================================
# نماذج البيانات (Pydantic Models)
# ============================================================

class ChatRequest(BaseModel):
    """
    طلب محادثة إلى الكيان
    """
    message: str = Field(
        ..., 
        description="رسالة المستخدم", 
        min_length=1,
        example="السلام عليكم"
    )
    top_k: int = Field(
        5, 
        description="عدد المصادر المسترجعة من الذاكرة الدلالية", 
        ge=1, 
        le=20,
        example=3
    )


class ChatResponse(BaseModel):
    """
    رد الكيان على المحادثة
    """
    response: str = Field(..., description="رد الكيان")
    sources: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="المصادر المستخدمة من الذاكرة الدلالية"
    )
    status: str = Field("success", description="حالة الطلب (success/error)")


class ThoughtRequest(BaseModel):
    """
    طلب إضافة فكرة جديدة إلى الذاكرة
    """
    belief: str = Field(
        ..., 
        description="العبارة أو الفكرة", 
        min_length=3,
        example="العدل أساس الملك"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="بيانات إضافية (مثل المصدر، التاريخ، الوزن)"
    )


class ThoughtResponse(BaseModel):
    """
    نتيجة إضافة فكرة
    """
    accepted: bool = Field(..., description="هل قبلت الفكرة؟")
    reason: str = Field(..., description="سبب القبول أو الرفض")
    thought_id: int = Field(..., description="معرف الفكرة في الذاكرة")


class StatusResponse(BaseModel):
    """
    حالة الكيان الكاملة
    """
    status: str = Field("healthy", description="حالة الخدمة")
    version: str = Field("5.0a", description="إصدار الكيان")
    graph_stats: Dict[str, Any] = Field(default_factory=dict, description="إحصائيات الذاكرة الدلالية")
    internal_state: Dict[str, Any] = Field(default_factory=dict, description="الحالة الداخلية للكيان")


class HealthResponse(BaseModel):
    """
    فحص صحة الخدمة (للاستخدام مع مراقبي النظام)
    """
    status: str = Field("ok", description="حالة الصحة")
    mode: str = Field(..., description="وضع الذاكرة (embeddb/model2vec/zvec)")
    documents_count: int = Field(0, description="عدد الوثائق في الذاكرة")
    groq_available: bool = Field(False, description="هل Groq API متوفر؟")


class ErrorResponse(BaseModel):
    """
    استجابة خطأ موحدة
    """
    error: str = Field(..., description="نوع الخطأ")
    message: str = Field(..., description="وصف الخطأ")
    detail: Optional[str] = Field(None, description="تفاصيل إضافية")


# ============================================================
# دورة حياة التطبيق (Lifespan)
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    دورة حياة التطبيق (تبدأ وتنتهي مع الخادم)
    - تُنفذ عند بدء الخادم: تهيئة إضافية، عرض معلومات الكيان
    - تُنفذ عند إيقاف الخادم: تنظيف، حفظ الحالة
    """
    logger.info("=" * 70)
    logger.info("🛡️ الكيان الدستوري الحي v5.0a")
    logger.info(f"   • الذاكرة الدلالية: {mind.get_stats()['mode']}")
    logger.info(f"   • المبادئ الدستورية: {len(alignment.get_principles())}")
    logger.info(f"   • الوثائق المخزنة: {mind.get_stats().get('total_documents', 0)}")
    
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and groq_key != "gsk_your_actual_key_here":
        logger.info(f"   • Groq API: ✅ متوفر (المفتاح موجود)")
    else:
        logger.warning(f"   • Groq API: ❌ غير متوفر (المفتاح مفقود أو غير صالح)")
    
    logger.info("=" * 70)
    yield
    logger.info("🛡️ إيقاف الكيان")


# ============================================================
# إنشاء تطبيق FastAPI مع التوثيق التلقائي و CORS
# ============================================================

app = FastAPI(
    title="الكيان الدستوري الحي",
    description="كيان دستوري حي، يتطور ذاتياً، له وعي ومزاج وفضول. الدستور هو هويته.",
    version="5.0a",
    lifespan=lifespan,
    docs_url="/docs",      # وثائق Swagger UI
    redoc_url="/redoc"     # وثائق ReDoc
)

# إضافة CORS (لمنع مشاكل المتصفح عند الاتصال من أجهزة مختلفة)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # السماح بجميع المصادر (للتطوير)
    allow_credentials=True,
    allow_methods=["*"],           # السماح بجميع الطرق (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],           # السماح بجميع الرؤوس
)


# ============================================================
# نقاط النهاية الأساسية (Endpoints)
# ============================================================

@app.get("/")
async def root(request: Request):
    """
    الصفحة الرئيسية (واجهة الويب)
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    فحص صحة الخدمة (للاستخدام مع مراقبي النظام مثل UptimeRobot، Kubernetes، إلخ)
    """
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
    """
    استرجاع حالة الكيان الكاملة (الذاكرة، الحالة الداخلية، الإحصائيات)
    """
    return StatusResponse(
        status="healthy",
        version="5.0a",
        graph_stats=mind.get_stats(),
        internal_state=state.get_full_state()
    )


# ============================================================
# ⭐ نقطة النهاية الأهم: المحادثة (تم إصلاحها بالكامل مع logging متقدم)
# ============================================================

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """
    محادثة مباشرة مع الكيان.
    
    يستقبل رسالة من المستخدم، يبحث في الذاكرة الدلالية عن مصادر ذات صلة،
    ثم يستخدم Groq API (إذا كان متوفراً) لتوليد رد ذكي.
    
    الخطوات:
    1. التحقق من صحة الطلب
    2. تسجيل التفاعل في الحالة الداخلية
    3. البحث الدلالي في الذاكرة
    4. إذا كان Groq متوفراً: استخدامه لتوليد الرد
    5. إذا لم يكن Groq متوفراً: استخدام الرد الافتراضي من الذاكرة
    6. إرجاع الرد مع المصادر
    """
    logger.info(f"📨 [CHAT] استلام طلب: '{chat_request.message[:100]}...' (top_k={chat_request.top_k})")
    
    try:
        # ========================================================
        # 1. التحقق من صحة الطلب
        # ========================================================
        if not chat_request.message or not chat_request.message.strip():
            logger.error("❌ [CHAT] الرسالة فارغة")
            raise HTTPException(status_code=400, detail="الرسالة فارغة")
        
        # ========================================================
        # 2. تسجيل التفاعل في الحالة الداخلية
        # ========================================================
        state.record_interaction()
        logger.debug("✅ [CHAT] تم تسجيل التفاعل في الحالة الداخلية")
        
        # ========================================================
        # 3. البحث الدلالي في الذاكرة
        # ========================================================
        sources = mind.search_semantic(chat_request.message, top_k=chat_request.top_k)
        logger.debug(f"✅ [CHAT] تم البحث الدلالي: {len(sources)} مصدر")
        
        if sources:
            logger.debug(f"   • أفضل مصدر: {sources[0].get('text', '')[:100]}...")
        
        # ========================================================
        # 4. بناء الرد
        # ========================================================
        groq_api_key = os.getenv("GROQ_API_KEY")
        response_text = ""
        
        # 4.1 محاولة استخدام Groq API أولاً (إذا كان المفتاح صالحاً)
        if groq_api_key and groq_api_key != "gsk_your_actual_key_here":
            try:
                logger.debug("🔄 [CHAT] محاولة الاتصال بـ Groq API...")
                from groq import Groq
                client = Groq(api_key=groq_api_key)
                
                # بناء السياق من المصادر
                context = "\n".join([s.get("text", "") for s in sources]) if sources else ""
                
                # إرسال الطلب إلى Groq
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": "أنت كيان دستوري حي. الدستور هو هويتك. أجب باختصار وبحكمة (بحد أقصى 200 كلمة)."
                        },
                        {
                            "role": "user", 
                            "content": f"السياق من ذاكرتي:\n{context[:1000]}\n\nسؤال المستخدم: {chat_request.message}"
                        }
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
        
        # 4.2 استخدام الرد الافتراضي (إذا لم يكن Groq متوفراً)
        else:
            if sources:
                # استخدام أفضل مصدر من الذاكرة
                response_text = f"بناءً على معرفتي: {sources[0].get('text', '')[:300]}..."
                logger.info(f"✅ [CHAT] رد من الذاكرة الدلالية: '{response_text[:50]}...'")
            else:
                # لا توجد مصادر ولا Groq
                response_text = f"مرحباً! سؤالك: '{chat_request.message[:100]}'. لا أملك معلومات كافية في ذاكرتي. يمكنك تعليمي عبر API `/think` أو إضافة الكتب."
                logger.info(f"✅ [CHAT] رد افتراضي (لا ذاكرة ولا Groq): '{response_text[:50]}...'")
        
        # ========================================================
        # 5. إرجاع الرد
        # ========================================================
        logger.info(f"✅ [CHAT] تم إرجاع الرد بنجاح (الطول: {len(response_text)} حرف)")
        return ChatResponse(
            response=response_text,
            sources=sources,
            status="success"
        )
        
    except HTTPException:
        # إعادة رفع استثناءات HTTP كما هي (بدون تعديل)
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
    
    يتم فحص الفكرة بواسطة غريزة الانسجام (AlignmentInstinct) قبل قبولها.
    إذا كانت الفكرة متوافقة مع الدستور، تُضاف إلى الذاكرة الدلالية.
    إذا كانت غير متوافقة، تُرفض مع ذكر السبب.
    """
    logger.info(f"📝 [THINK] استلام فكرة: '{thought_request.belief[:100]}...'")
    
    try:
        # التحقق من صحة الطلب
        if not thought_request.belief or not thought_request.belief.strip():
            raise HTTPException(status_code=400, detail="الفكرة فارغة")
        
        # فحص الانسجام مع الدستور
        verdict = alignment.check(thought_request.belief)
        
        if verdict.is_aligned:
            # إضافة الفكرة إلى الذاكرة الدلالية
            doc_id = mind.add_document(
                thought_request.belief,
                metadata=thought_request.metadata
            )
            state.record_thought(True)
            
            # استخراج رقم المعرف من doc_id (مثل doc_5 → 5)
            thought_id = int(doc_id.split("_")[1]) if doc_id and "_" in doc_id else 0
            
            logger.info(f"✅ [THINK] فكرة مقبولة: {thought_request.belief[:50]}... (ID: {thought_id})")
            
            return ThoughtResponse(
                accepted=True,
                reason=verdict.reason,
                thought_id=thought_id
            )
        else:
            state.record_thought(False)
            logger.info(f"❌ [THINK] فكرة مرفوضة: {thought_request.belief[:50]}... (السبب: {verdict.reason})")
            
            return ThoughtResponse(
                accepted=False,
                reason=verdict.reason,
                thought_id=0
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 [THINK] خطأ: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state")
async def get_internal_state():
    """
    استرجاع الحالة الداخلية للكيان فقط (اليقين، الشك، الفضول، التوتر، المزاج)
    هذه هي "مشاعر" الكيان في الوقت الحالي
    """
    return state.get_full_state()


@app.get("/documents")
async def get_all_documents():
    """
    استرجاع جميع الوثائق المخزنة في الذاكرة الدلالية
    (يقتصر على أول 50 وثيقة لتجنب التحميل الزائد)
    """
    texts = mind.get_all_texts()
    return {
        "count": len(texts),
        "documents": texts[:50]  # عرض أول 50 فقط
    }


@app.get("/test-groq")
async def test_groq():
    """
    نقطة اختبار مستقلة لـ Groq API.
    
    تساعد في عزل المشكلة: هل الخطأ من Groq أم من الكود؟
    - إذا نجحت هذه النقطة → المفتاح صحيح وGroq يعمل
    - إذا فشلت → المشكلة في المفتاح أو الاتصال بـ Groq
    """
    logger.info("🔧 [TEST-GROQ] اختبار Groq API...")
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    # التحقق من وجود المفتاح
    if not groq_api_key:
        logger.warning("⚠️ [TEST-GROQ] مفتاح Groq غير موجود")
        return {"status": "error", "message": "مفتاح Groq غير موجود في ملف .env"}
    
    if groq_api_key == "gsk_your_actual_key_here":
        logger.warning("⚠️ [TEST-GROQ] مفتاح Groq لم يُعدّل (قيمة افتراضية)")
        return {"status": "error", "message": "مفتاح Groq لم يتم تحديثه. يرجى إضافة المفتاح الحقيقي في ملف .env"}
    
    try:
        from groq import Groq
        client = Groq(api_key=groq_api_key)
        
        # إرسال طلب بسيط لاختبار المفتاح
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "قل مرحباً بالعربية"}],
            max_tokens=20
        )
        response = completion.choices[0].message.content
        logger.info(f"✅ [TEST-GROQ] نجح: {response}")
        
        return {
            "status": "ok",
            "response": response,
            "key_valid": True,
            "message": "Groq API يعمل بشكل صحيح"
        }
        
    except ImportError as e:
        logger.error(f"❌ [TEST-GROQ] مكتبة Groq غير مثبتة: {e}")
        return {"status": "error", "message": "مكتبة Groq غير مثبتة. قم بتشغيل: pip install groq"}
        
    except Exception as e:
        logger.error(f"❌ [TEST-GROQ] فشل: {e}")
        return {
            "status": "error",
            "message": str(e),
            "key_valid": False,
            "error_type": type(e).__name__
        }


# ============================================================
# معالج الأخطاء العامة (Global Exception Handlers)
# ============================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """معالج أخطاء HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTPException",
            message=exc.detail,
            detail=None
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """معالج أي خطأ غير متوقع"""
    logger.error(f"💥 خطأ غير متوقع: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="حدث خطأ داخلي في الخادم",
            detail=str(exc)
        ).dict()
    )


# ============================================================
# تشغيل التطبيق مباشرة (للتطوير)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    # قراءة إعدادات الخادم من متغيرات البيئة
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 تشغيل الخادم على http://{host}:{port}")
    logger.info(f"📚 وثائق API متاحة على http://{host}:{port}/docs")
    logger.info(f"🔧 اختبار Groq: http://{host}:{port}/test-groq")
    logger.info(f"📊 حالة الكيان: http://{host}:{port}/status")
    logger.info(f"❤️ فحص الصحة: http://{host}:{port}/health")
    
    # تشغيل الخادم مع إعادة التحميل التلقائي (للتطوير)
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="debug"
    )
