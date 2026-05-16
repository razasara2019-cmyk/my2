import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from app.config import GROQ_API_KEY, GITHUB_TOKEN, PERSISTENT_DIR
from app.agent.living_mind import LivingMind
from app.api.chat import router as chat_router
from app.api.books import router as books_router
from app.api.status import router as status_router
from app.git_backup.backup import restore_agent_state, backup_agent_state

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
    logger.info("🛡️ تشغيل الحارس الصامت")
    logger.info("=" * 50)

    os.makedirs(PERSISTENT_DIR, exist_ok=True)
    os.makedirs(f"{PERSISTENT_DIR}/books", exist_ok=True)

    restore_agent_state()

    if GROQ_API_KEY:
        logger.info("✅ Groq API: متوفر")
    else:
        logger.warning("⚠️ Groq API: غير متوفر")

    if GITHUB_TOKEN:
        logger.info("✅ GitHub Backup: متوفر")
    else:
        logger.warning("⚠️ GitHub Backup: غير متوفر")

    _mind = LivingMind()
    app.state.mind = _mind

    logger.info("✅ الوكيل جاهز")
    yield

    if _mind:
        _mind.close()
    backup_agent_state("shutdown")
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
app.include_router(books_router)
app.include_router(status_router)

templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "alive", "version": "2.0.0"}


@app.post("/manual-backup")
async def manual_backup():
    backup_agent_state("manual")
    return {"status": "success"}
