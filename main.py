"""
main.py – الكيان الدستوري الحي مع Groq API ومحرك الدافع الداخلي
الإصدار: 5.1.0 (متكامل)
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
from mind.drive_engine import InternalDriveEngine
from mind.reflective_engine import ReflectiveEngine

# ============================================================
# التهيئة الأساسية
# ============================================================

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

# تهيئة المكونات الأساسية
logger.info("🔄 جاري تهيئة الكيان الدستوري الحي v5.1.0...")

mind = GraphMind()
alignment = AlignmentInstinct()
state = InternalState()
templates = Jinja2Templates(directory="templates")

# تهيئة محرك التفكر ومحرك الدافع الداخلي
reflective = ReflectiveEngine(graph_mind=mind, alignment_instinct=alignment)
drive_engine = InternalDriveEngine(internal_state=state, reflective_engine=reflective)

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_AVAILABLE = bool(GROQ_API_KEY and GROQ_API_KEY != "gsk_your_actual_key_here")

if GROQ_AVAILABLE:
    logger.info(f"✅ Groq API متوفر (النموذج: {GROQ_MODEL})")
else:
    logger.warning("⚠️ Groq API غير متوفر. تحقق من GROQ_API_KEY في ملف .env")

logger.info("✅ تم تهيئة جميع المكونات بنجاح")


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


class ThoughtRequest(BaseModel):
    belief: str = Field(..., min_length=3)
    metadata: Optional[Dict[str, Any]] = None


class ThoughtResponse(BaseModel):
    accepted: bool
    reason: str
    thought_id: int


# ============================================================
# دورة حياة التطبيق (Lifespan)
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("🛡️ الكيان الدستوري الحي v5.1.0")
    logger.info(f"   • الذاكرة: {mind.get_stats()['mode']}")
    logger.info(f"   • المبادئ الدستورية: {len(alignment.get_principles())}")
    logger.info(f"   • Groq API: {'✅ متوفر (' + GROQ_MODEL + ')' if GROQ_AVAILABLE else '❌ غير متوفر'}")
    logger.info("=" * 60)
    
    # بدء محرك الدافع الداخلي
    drive_engine.start()
    logger.info("🫀 محرك الدافع الداخلي يعمل في الخلفية")
    
    yield
    
    # إيقاف محرك الدافع
    drive_engine.stop()
    logger.info("🛡️ إيقاف الكيان")


# ============================================================
# تطبيق FastAPI
# ============================================================

app = FastAPI(
    title="الكيان الدستوري الحي",
    version="5.1.0",
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
# وظيفة مساعدة لاستدعاء Groq
# ============================================================

def call_groq(prompt: str, system_prompt: str = None) -> Optional[str]:
    """استدعاء Groq API وإرجاع الرد"""
    if not GROQ_AVAILABLE:
        return None
    
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ خطأ في Groq API: {e}")
        return None


# ============================================================
# نقاط النهاية (Endpoints)
# ============================================================

@app.get("/")
async def root(request: Request):
    """الصفحة الرئيسية (واجهة الويب)"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """فحص صحة الخدمة"""
    stats = mind.get_stats()
    return {
        "status": "ok",
        "mode": stats.get("mode", "fastembed"),
        "documents_count": stats.get("total_documents", 0),
        "groq_available": GROQ_AVAILABLE,
        "groq_model": GROQ_MODEL if GROQ_AVAILABLE else None,
        "drive_engine_running": drive_engine.running
    }


@app.get("/status")
async def get_status():
    """حالة الكيان الكاملة"""
    return {
        "status": "healthy",
        "version": "5.1.0",
        "graph_stats": mind.get_stats(),
        "internal_state": state.get_full_state(),
        "groq": {
            "available": GROQ_AVAILABLE,
            "model": GROQ_MODEL if GROQ_AVAILABLE else None
        }
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """محادثة مباشرة مع الكيان"""
    try:
        logger.info(f"📨 استلام طلب: {chat_request.message[:50]}...")
        
        if not chat_request.message or not chat_request.message.strip():
            raise HTTPException(status_code=400, detail="الرسالة فارغة")
        
        state.record_interaction()
        
        # البحث في الذاكرة الدلالية
        sources = mind.search_semantic(chat_request.message, top_k=chat_request.top_k)
        
        # بناء السياق من الذاكرة
        context = ""
        if sources:
            context = "\n".join([f"- {s.get('text', '')[:300]}" for s in sources[:3]])
        
        # إعداد النظام prompt
        system_prompt = """أنت الكيان الدستوري الحي. لديك دستور ثابت من المبادئ:
- التوحيد: الإخلاص والتوحيد
- العدل: الإنصاف والمساواة
- الرحمة: التعاطف واللين
- الصدق: الصراحة والأمانة
- الأمانة: الوفاء بالعهد

أجب باختصار (بحد أقصى 3-4 جمل). كن حكيماً وعادلاً ورحيماً. لا تخرج عن الدستور."""

        # إعداد رسالة المستخدم
        user_prompt = chat_request.message
        if context:
            user_prompt = f"""السياق من ذاكرتي:
{context}

سؤال المستخدم: {chat_request.message}

أجب بناءً على السياق إن كان مفيداً، وإلا أجب من معرفتك الخاصة. كن مختصراً."""

        # محاولة استخدام Groq
        response_text = call_groq(user_prompt, system_prompt)
        
        # الرد الاحتياطي إذا فشل Groq
        if response_text is None:
            if sources:
                response_text = sources[0]['text'][:300]
                if len(sources) > 1:
                    response_text += "\n\n(يمكنني تقديم المزيد من المعلومات إذا أردت)"
            else:
                response_text = f"مرحباً! سؤالك: '{chat_request.message[:100]}'. لا أملك معلومات كافية في ذاكرتي حالياً. يمكنك تعليمي عبر إضافة معارف جديدة باستخدام API /think."
            logger.warning("⚠️ استخدام الرد الاحتياطي (Groq غير متوفر)")
        else:
            logger.info(f"✅ رد من Groq: {response_text[:100]}...")
        
        return ChatResponse(response=response_text, sources=sources, status="success")
        
    except Exception as e:
        logger.error(f"❌ خطأ في /chat: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/think", response_model=ThoughtResponse)
async def add_thought(thought_request: ThoughtRequest):
    """إضافة فكرة جديدة إلى الكيان (يتم فحصها ضد الدستور)"""
    if not thought_request.belief or not thought_request.belief.strip():
        raise HTTPException(status_code=400, detail="الفكرة فارغة")
    
    verdict = alignment.check(thought_request.belief)
    
    if verdict.is_aligned:
        doc_id = mind.add_document(thought_request.belief, metadata=thought_request.metadata)
        state.record_thought(True)
        thought_id = int(doc_id.split("_")[1]) if doc_id and "_" in doc_id else 0
        logger.info(f"✅ فكرة مقبولة: {thought_request.belief[:50]}...")
        return ThoughtResponse(accepted=True, reason=verdict.reason, thought_id=thought_id)
    else:
        state.record_thought(False)
        for principle in verdict.conflicting_principles:
            state.record_contradiction(principle)
        logger.info(f"❌ فكرة مرفوضة: {thought_request.belief[:50]}... (السبب: {verdict.reason})")
        return ThoughtResponse(accepted=False, reason=verdict.reason, thought_id=0)


@app.get("/state")
async def get_internal_state():
    """الحالة الداخلية الكاملة للكيان"""
    return state.get_full_state()


@app.get("/mood")
async def get_mood():
    """ملخص سريع عن مزاج الكيان"""
    return {
        "mood": state.mood,
        "summary": state.get_mood_summary(),
        "certainty": state.certainty,
        "curiosity": state.curiosity,
        "tension": state.internal_tension
    }


@app.get("/documents")
async def get_all_documents():
    """جميع الوثائق المخزنة في الذاكرة"""
    texts = mind.get_all_texts()
    return {"count": len(texts), "documents": texts[:50]}


@app.get("/principles")
async def get_principles():
    """المبادئ الدستورية للكيان"""
    return {
        "status": "success",
        "count": len(alignment.get_principles()),
        "principles": alignment.get_principles(),
        "core_stats": alignment.get_core_stats()
    }


@app.get("/drive-stats")
async def get_drive_stats():
    """إحصائيات محرك الدافع الداخلي"""
    return drive_engine.get_stats()


@app.post("/trigger-drive/{drive_type}")
async def trigger_drive(drive_type: str):
    """إطلاق دافع داخلي فوري (للاختبار)"""
    valid_drives = ["investigate", "reinforce", "contemplate", "resolve_tension", "explore"]
    if drive_type not in valid_drives:
        raise HTTPException(status_code=400, detail=f"نوع دافع غير صالح. اختر من: {valid_drives}")
    
    drive_engine.trigger_immediate_drive(drive_type)
    return {"status": "triggered", "drive_type": drive_type}


@app.get("/test-groq")
async def test_groq():
    """نقطة اختبار مخصصة لـ Groq API"""
    if not GROQ_AVAILABLE:
        return {
            "status": "error", 
            "message": "Groq API غير متوفر. تحقق من GROQ_API_KEY في ملف .env",
            "key_present": bool(GROQ_API_KEY),
            "key_valid": GROQ_AVAILABLE
        }
    
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": "قل مرحبا بالعربية"}],
            max_tokens=20
        )
        return {
            "status": "ok", 
            "response": completion.choices[0].message.content,
            "model": GROQ_MODEL
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================
# التشغيل المباشر
# ============================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 تشغيل الخادم على http://{host}:{port}")
    logger.info(f"📚 وثائق API: http://{host}:{port}/docs")
    logger.info(f"🔧 اختبار Groq: http://{host}:{port}/test-groq")
    logger.info(f"📊 حالة الكيان: http://{host}:{port}/status")
    logger.info(f"🫀 محرك الدافع: http://{host}:{port}/drive-stats")
    
    uvicorn.run("main:app", host=host, port=port, reload=False)
