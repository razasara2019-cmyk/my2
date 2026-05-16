import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import GROQ_API_KEY
from app.agent.living_mind import LivingMind
from app.api.chat import router as chat_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_mind = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _mind
    logger.info("=" * 40)
    logger.info("🛡️ تشغيل الحارس الصامت")
    logger.info("=" * 40)

    if GROQ_API_KEY:
        logger.info("✅ Groq API: متوفر")
    else:
        logger.warning("⚠️ Groq API: غير متوفر")

    _mind = LivingMind()
    app.state.mind = _mind
    logger.info("✅ الوكيل جاهز")
    yield
    if _mind:
        _mind.close()
    logger.info("🛡️ إغلاق الحارس الصامت")


app = FastAPI(title="الحارس الصامت", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    # واجهة HTML مدمجة مباشرة (بدون الحاجة إلى مجلد templates)
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>الحارس الصامت</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #1a1a2e; margin: 0; padding: 20px; }
            .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; }
            .header { background: #0f3460; color: white; padding: 15px; text-align: center; }
            .chat { height: 400px; overflow-y: auto; padding: 15px; background: #f5f5f5; }
            .user { text-align: right; margin: 10px 0; }
            .user span { background: #007bff; color: white; padding: 10px 15px; border-radius: 20px; display: inline-block; }
            .agent { text-align: left; margin: 10px 0; }
            .agent span { background: #e9ecef; color: #333; padding: 10px 15px; border-radius: 20px; display: inline-block; }
            .input-area { display: flex; padding: 15px; background: white; border-top: 1px solid #ddd; }
            input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 25px; margin-left: 10px; }
            button { background: #0f3460; color: white; border: none; padding: 10px 20px; border-radius: 25px; cursor: pointer; }
            .footer { text-align: center; padding: 10px; font-size: 12px; color: #888; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ الحارس الصامت</h1>
                <p>وكيل دستوري حي | يتعلم | يتطور | صامت</p>
            </div>
            <div class="chat" id="chat">
                <div class="agent"><span>السلام عليكم. أنا الحارس الصامت. اسأل ما شئت.</span></div>
            </div>
            <div class="input-area">
                <input type="text" id="question" placeholder="اكتب سؤالك..." onkeypress="if(event.keyCode==13) send()">
                <button onclick="send()">إرسال</button>
            </div>
            <div class="footer">الإصدار 2.0.0 | يعمل بـ FAISS + Groq</div>
        </div>
        <script>
            const chat = document.getElementById('chat');
            const input = document.getElementById('question');
            
            function addMessage(text, isUser) {
                const div = document.createElement('div');
                div.className = isUser ? 'user' : 'agent';
                div.innerHTML = '<span>' + text + '</span>';
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }
            
            async function send() {
                const question = input.value.trim();
                if (!question) return;
                addMessage(question, true);
                input.value = '';
                addMessage('✨ جاري التفكير...', false);
                try {
                    const res = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: question })
                    });
                    const data = await res.json();
                    chat.removeChild(chat.lastChild);
                    addMessage(data.response, false);
                } catch(e) {
                    chat.removeChild(chat.lastChild);
                    addMessage('❌ حدث خطأ، حاول مرة أخرى', false);
                }
            }
        </script>
    </body>
    </html>
    """


@app.get("/health")
async def health():
    return {"status": "alive", "version": "2.0.0"}


@app.get("/status")
async def status():
    if _mind:
        return _mind.get_status()
    return {"status": "starting"}
