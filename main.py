"""
main.py – نقطة الدخول الرئيسية للكيان الدستوري الحي
الإصدار: 5.0a النهائي (تم إصلاح خطأ المحادثة)
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from mind.graph_mind import GraphMind
from mind.alignment_instinct import AlignmentInstinct
from mind.internal_state import InternalState

# ============================================================
# التهيئة الأساسية
# ============================================================

# تحميل متغيرات البيئة
load_dotenv()

# تهيئة التسجيل (logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

# تهيئة المكونات الأساسية للكيان
mind = GraphMind()
alignment = AlignmentInstinct()
state = InternalState()

# تهيئة القوالب (templates)
templates = Jinja2Templates(directory="templates")


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
    sources: list = Field(default_factory=list, description="المصادر المستخدمة")
    status: str = Field("success", description="حالة الطلب")


class ThoughtRequest(BaseModel):
    """طلب إضافة فكرة جديدة إلى الذاكرة"""
    belief: str = Field(..., description="العبارة أو الفكرة", min_length=3)
    metadata: Optional[dict] = Field(default=None, description="بيانات إضافية")


class ThoughtResponse(BaseModel):
    """نتيجة إضافة فكرة"""
    accepted: bool = Field(..., description="هل قبلت الفكرة؟")
    reason: str = Field(..., description="سبب القبول أو الرفض")
    thought_id: int = Field(..., description="معرف الفكرة")


class StatusResponse(BaseModel):
    """حالة الكيان الكاملة"""
    status: str = Field("healthy", description="حالة الخدمة")
    version: str = Field("5.0a", description="إصدار الكيان")
    graph_stats: dict = Field(default_factory=dict, description="إحصائيات الذاكرة")
    internal_state: dict = Field(default_factory=dict, description="الحالة الداخلية")


class HealthResponse(BaseModel):
    """فحص صحة الخدمة"""
    status: str = Field("ok", description="حالة الصحة")
    mode: str = Field(..., description="وضع الذاكرة")
    documents_count: int = Field(0, description="عدد الوثائق في الذاكرة")


# ============================================================
# دورة حياة التطبيق (Lifespan)
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """دورة حياة التطبيق (تبدأ وتنتهي مع الخادم)"""
    logger.info("=" * 60)
    logger.info("🛡️ الكيان الدستوري الحي v5.0a")
    logger.info(f"   • الذاكرة: {mind.get_stats()['mode']}")
    logger.info(f"   • المبادئ الدستورية: {len(alignment.get_principles())}")
    groq_key = os.getenv("GROQ_API_KEY")
    logger.info(f"   • Groq API: {'✅ متوفر' if groq_key else '❌ غير متوفر (لن تعمل المحادثة)'}")
    logger.info("=" * 60)
    yield
    logger.info("🛡️ إيقاف الكيان")


# ============================================================
# إنشاء تطبيق FastAPI
# ============================================================

app = FastAPI(
    title="الكيان الدستوري الحي",
    description="كيان دستوري حي، يتطور ذاتياً، له وعي ومزاج وفضول",
    version="5.0a",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# ============================================================
# نقاط النهاية (Endpoints)
# ============================================================

@app.get("/")
async def root(request: Request):
    """الصفحة الرئيسية (واجهة الويب)"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """فحص صحة الخدمة (للاستخدام مع مراقبي النظام)"""
    stats = mind.get_stats()
    return HealthResponse(
        status="ok",
        mode=stats.get("mode", "embeddb"),
        documents_count=stats.get("total_documents", 0)
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
# نقطة النهاية الأهم: المحادثة (تم إصلاحها)
# ============================================================

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """
    محادثة مباشرة مع الكيان.
    يستقبل رسالة ويعيد رداً بناءً على الذاكرة الدلالية و Groq API.
    """
    if not chat_request.message or not chat_request.message.strip():
        raise HTTPException(status_code=400, detail="الرسالة فارغة")
    
    # تسجيل التفاعل
    state.record_interaction()
    
    # البحث الدلالي في الذاكرة
    sources = mind.search_semantic(chat_request.message, top_k=chat_request.top_k)
    
    # بناء السياق من المصادر
    context = "\n".join([s.get("text", "") for s in sources]) if sources else ""
    
    # الحصول على مفتاح Groq
    groq_api_key = os.getenv("GROQ_API_KEY")
    response_text = ""
    
    if groq_api_key and groq_api_key != "gsk_your_actual_key_here":
        # استخدام Groq API للإجابة
        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            
            system_prompt = """أنت كيان دستوري حي. الدستور هو هويتك.
أجب من معرفتك الداخلية. كن دقيقاً وحكيماً.
إذا كان السؤال خارج دستورك، قل بصدق "لا أعرف".
لا تذكر أنك نموذج لغوي. أنت كيان حي."""
            
            user_prompt = f"""السياق من ذاكرتك:
{context[:1500]}

سؤال المستخدم: {chat_request.message}

أجب باقتضاب وبحكمة (بحد أقصى 200 كلمة):"""
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            response_text = completion.choices[0].message.content
            logger.info(f"💬 رد Groq: {response_text[:50]}...")
            
        except Exception as e:
            logger.error(f"خطأ في Groq: {e}")
            response_text = "عذراً، حدث خطأ في معالجة طلبك. تأكد من صحة مفتاح Groq API."
    else:
        # رد بسيط بدون Groq (يعتمد على المصادر فقط)
        if sources:
            response_text = f"بناءً على معرفتي: {sources[0].get('text', '')[:200]}..."
            logger.info(f"💬 رد من الذاكرة: {response_text[:50]}...")
        else:
            response_text = f"مرحباً! سؤالك: '{chat_request.message}'. لا أملك معلومات كافية في ذاكرتي. يمكنك تعليمي عبر إضافة الكتب أو استخدام API `/think`."
            logger.info(f"💬 رد افتراضي (لا ذاكرة): {response_text[:50]}...")
    
    return ChatResponse(
        response=response_text,
        sources=sources,
        status="success"
    )


# ============================================================
# نقاط النهاية الأخرى
# ============================================================

@app.post("/think", response_model=ThoughtResponse)
async def add_thought(thought_request: ThoughtRequest):
    """
    إضافة فكرة جديدة إلى الكيان.
    يتم فحصها بواسطة غريزة الانسجام قبل القبول.
    """
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
        
        # استخراج رقم المعرف
        thought_id = int(doc_id.split("_")[1]) if doc_id and "_" in doc_id else 0
        
        logger.info(f"✅ فكرة مقبولة: {thought_request.belief[:50]}...")
        
        return ThoughtResponse(
            accepted=True,
            reason=verdict.reason,
            thought_id=thought_id
        )
    else:
        state.record_thought(False)
        logger.info(f"❌ فكرة مرفوضة: {thought_request.belief[:50]}... (السبب: {verdict.reason})")
        
        return ThoughtResponse(
            accepted=False,
            reason=verdict.reason,
            thought_id=0
        )


@app.get("/state")
async def get_internal_state():
    """استرجاع الحالة الداخلية للكيان"""
    return state.get_full_state()


@app.get("/documents")
async def get_all_documents():
    """استرجاع جميع الوثائق المخزنة في الذاكرة"""
    texts = mind.get_all_texts()
    return {
        "count": len(texts),
        "documents": texts[:50]
    }


# ============================================================
# تشغيل التطبيق
# ============================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 تشغيل الخادم على {host}:{port}")
    logger.info(f"📚 وثائق API متاحة على http://{host}:{port}/docs")
    uvicorn.run("main:app", host=host, port=port, reload=True)
