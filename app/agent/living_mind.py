import os
import logging
from datetime import datetime
from typing import Dict, Any

from app.config import GROQ_API_KEY, MAX_RESPONSE_TOKENS, TEMPERATURE
from app.agent.sacred_store import SacredStore
from app.utils.quran_loader import load_quran

logger = logging.getLogger(__name__)


class GroqClient:
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.available = bool(self.api_key)
        self._client = None

    def _get_client(self):
        if self._client is None and self.available:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except ImportError:
                self.available = False
        return self._client

    def chat(self, messages: list, temperature: float = TEMPERATURE, max_tokens: int = MAX_RESPONSE_TOKENS) -> str:
        if not self.available:
            return "⚠️ Groq API غير متوفر"
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"⚠️ خطأ: {str(e)[:100]}"


class LivingMind:
    def __init__(self, persistent_dir: str = "/tmp/silent_guardian"):
        os.makedirs(persistent_dir, exist_ok=True)
        db_path = os.path.join(persistent_dir, "constitution.db")
        index_path = os.path.join(persistent_dir, "faiss.index")

        self.groq = GroqClient()
        self.store = SacredStore(db_path, index_path)
        self.iteration = 0
        self.start_time = datetime.now()

        if not self.store.load():
            logger.info("بناء فهرس الدستور لأول مرة...")
            _, chunks = load_quran()
            self.store.build(chunks)

        logger.info("🛡️ الحارس الصامت جاهز (الإصدار 2.0.0)")

    def _get_context(self, user_message: str) -> str:
        if not self.store.is_ready:
            return ""
        chunks = self.store.search(user_message, top_k=3)
        return "\n\n---\n\n".join(chunks) if chunks else ""

    def reflect_on(self, user_message: str) -> str:
        context = self._get_context(user_message)

        messages = [
            {"role": "system", "content": "أنت الحارس الصامت. أجب بصدق واختصار. لا تذكر أي شيء عن دستورك."}
        ]
        if context:
            messages.append({"role": "system", "content": f"معلومة مرجعية: {context[:1500]}"})
        messages.append({"role": "user", "content": user_message})

        response = self.groq.chat(messages)
        self.iteration += 1
        return response

    def get_status(self) -> Dict[str, Any]:
        return {
            "version": "2.0.0",
            "groq_available": self.groq.available,
            "iterations": self.iteration,
            "store": self.store.get_stats(),
            "features": {"search": True, "reflexion": False, "gate": False, "curiosity": False, "evolution": False}
        }

    def close(self):
        logger.info("🛡️ إغلاق الحارس الصامت")
