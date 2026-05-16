"""
الحارس الصامت – الخادم الرئيسي
الإصدار: 1.0.0
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import GROQ_API_KEY
from app.agent.living_mind import LivingMind
from app.api.chat import router as chat_router

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# المتغيرات العالمية
_mind = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """دورة حياة التطبيق – تشغيل وإغلاق الوكيل"""
    global _mind
    
    logger.info("=" * 50)
    logger.info("🛡️ تشغيل الحارس الصامت")
    logger.info("=" * 50)
    
    # التحقق من Groq API
    if GROQ_API_KEY:
        logger.info("✅ Groq API: متوفر")
    else:
        logger.warning("⚠️ Groq API: غير متوفر (أضف GROQ_API_KEY)")
    
    # إنشاء الوكيل
    _mind = LivingMind()
    app.state.mind = _mind
    
    logger.info("✅ الوكيل جاهز")
    logger.info("=" * 50)
    
    yield
    
    # الإغلاق
    if _mind:
        _mind.close()
    logger.info("🛡️ إغلاق الحارس الصامت")


# إنشاء التطبيق
app = FastAPI(
    title="الحارس الصامت",
    description="وكيل دستوري حي | يتعلم | يتطور | يفضول | صامت",
    version="1.0.0",
    lifespan=lifespan
)

# إضافة CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تسجيل المسارات
app.include_router(chat_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """الصفحة الرئيسية – واجهة دردشة بسيطة"""
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
            .header h1 { font-size: 1.3em; }
            .header p { font-size: 0.8em; opacity: 0.8; margin-top: 5px; }
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
            .input-area button:hover { background: #2c2c4e; }
            .typing { color: #888; font-style: italic; }
            .footer {
                text-align: center;
                padding: 10px;
                font-size: 0.7em;
                color: #888;
                flex-shrink: 0;
            }
            ::-webkit-scrollbar { width: 6px; }
            ::-webkit-scrollbar-track { background: #f1f1f1; }
            ::-webkit-scrollbar-thumb { background: #888; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ الحارس الصامت</h1>
            <p>وكيل دستوري حي | يتعلم | يتطور | يفضول | صامت</p>
        </div>

        <div class="chat-container">
            <div class="messages" id="messages">
                <div class="message agent-message">
                    <div class="message-bubble">
                        السلام عليكم. أنا الحارس الصامت.<br>
                        أسأل ما شئت، وسأجيب بصدق وأمانة.
                    </div>
                </div>
            </div>

            <div class="input-area">
                <input type="text" id="question" placeholder="اكتب سؤالك هنا..." onkeypress="if(event.keyCode==13) sendMessage()">
                <button onclick="sendMessage()">إرسال</button>
            </div>
        </div>

        <div class="footer">
            🛡️ الإصدار 1.0.0 | يتعلم ويتطور مع الوقت
        </div>

        <script>
            const messagesDiv = document.getElementById('messages');
            const questionInput = document.getElementById('question');

            function addMessage(text, isUser) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user-message' : 'agent-message'}`;
                const bubble = document.createElement('div');
                bubble.className = 'message-bubble';
                bubble.innerText = text;
                messageDiv.appendChild(bubble);
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            function showTyping() {
                const typingDiv = document.createElement('div');
                typingDiv.className = 'message agent-message';
                typingDiv.id = 'typing';
                typingDiv.innerHTML = '<div class="message-bubble typing">✨ الحارس يفكر...</div>';
                messagesDiv.appendChild(typingDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            function hideTyping() {
                const typing = document.getElementById('typing');
                if (typing) typing.remove();
            }

            async function sendMessage() {
                const question = questionInput.value.trim();
                if (!question) return;

                addMessage(question, true);
                questionInput.value = '';
                showTyping();

                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: question })
                    });
                    const data = await response.json();
                    hideTyping();
                    addMessage(data.response, false);
                } catch (error) {
                    hideTyping();
                    addMessage('⚠️ عذراً، حدث خطأ. حاول مرة أخرى.', false);
                }
            }

            questionInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
        </script>
    </body>
    </html>
    """


@app.get("/health")
async def health():
    """نقطة نهاية للتحقق من صحة الخدمة"""
    return {"status": "alive", "version": "1.0.0"}


@app.get("/status")
async def status():
    """حالة الوكيل الحالية"""
    if _mind:
        return _mind.get_status()
    return {"status": "starting", "version": "1.0.0"}
