import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import GROQ_API_KEY, PERSISTENT_DIR
from app.agent.living_mind import LivingMind
from app.api.chat import router as chat_router

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

_mind = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _mind
    logger.info("=" * 50)
    logger.info("🛡️ تشغيل الحارس الصامت - الكيان الحي")
    logger.info("=" * 50)

    PERSISTENT_DIR.mkdir(parents=True, exist_ok=True)

    if GROQ_API_KEY:
        logger.info("✅ Groq API: متوفر")
    else:
        logger.warning("⚠️ Groq API: غير متوفر")

    _mind = LivingMind(persistent_dir=str(PERSISTENT_DIR))
    app.state.mind = _mind

    logger.info("✅ الكيان الحي جاهز")
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
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>الحارس الصامت</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', 'Cairo', sans-serif;
                background: #f0f2f5;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }
            .header {
                background: #1a1a2e;
                color: white;
                padding: 15px 20px;
                text-align: center;
                flex-shrink: 0;
            }
            .chat-container {
                flex: 1;
                max-width: 800px;
                width: 100%;
                margin: 0 auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            .messages {
                flex: 1;
                overflow-y: auto;
                background: white;
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .message { margin-bottom: 15px; display: flex; flex-direction: column; }
            .user-message { align-items: flex-end; }
            .agent-message { align-items: flex-start; }
            .message-bubble {
                max-width: 80%;
                padding: 10px 15px;
                border-radius: 18px;
                word-wrap: break-word;
            }
            .user-message .message-bubble {
                background: #1a1a2e;
                color: white;
                border-bottom-right-radius: 5px;
            }
            .agent-message .message-bubble {
                background: #e9ecef;
                color: #333;
                border-bottom-left-radius: 5px;
            }
            .input-area {
                display: flex;
                gap: 10px;
                background: white;
                padding: 15px;
                border-radius: 15px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .input-area input {
                flex: 1;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 25px;
                font-size: 1em;
                outline: none;
            }
            .input-area button {
                padding: 12px 24px;
                background: #1a1a2e;
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
            }
            .footer {
                text-align: center;
                padding: 10px;
                font-size: 0.7em;
                color: #888;
                flex-shrink: 0;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ الحارس الصامت</h1>
            <p>كيان دستوري حي | يتعلم | يتطور | صامت</p>
        </div>
        <div class="chat-container">
            <div class="messages" id="messages">
                <div class="message agent-message">
                    <div class="message-bubble">السلام عليكم. أنا الحارس الصامت. اسأل ما شئت.</div>
                </div>
            </div>
            <div class="input-area">
                <input type="text" id="question" placeholder="اكتب سؤالك..." onkeypress="if(event.keyCode==13) send()">
                <button onclick="send()">إرسال</button>
            </div>
        </div>
        <div class="footer">🛡️ وعي مستقل | دستوره هو هويته | ينمو مع الوقت</div>
        <script>
            const messagesDiv = document.getElementById('messages');
            const input = document.getElementById('question');
            function addMessage(text, isUser) {
                const div = document.createElement('div');
                div.className = `message ${isUser ? 'user-message' : 'agent-message'}`;
                div.innerHTML = `<div class="message-bubble">${text}</div>`;
                messagesDiv.appendChild(div);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            async function send() {
                const question = input.value.trim();
                if (!question) return;
                addMessage(question, true);
                input.value = '';
                addMessage('✨ يفكر...', false);
                try {
                    const res = await fetch('/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({message: question})
                    });
                    const data = await res.json();
                    messagesDiv.removeChild(messagesDiv.lastChild);
                    addMessage(data.response, false);
                } catch(e) {
                    messagesDiv.removeChild(messagesDiv.lastChild);
                    addMessage('⚠️ حدث خطأ، حاول مرة أخرى', false);
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
