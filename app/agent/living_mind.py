"""
الحارس الصامت – قلب الوكيل الحي
الإصدار: 1.0.0 (الأساس)
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.config import GROQ_API_KEY, MAX_RESPONSE_TOKENS, TEMPERATURE

logger = logging.getLogger(__name__)


class GroqClient:
    """عميل Groq – مسؤول عن الذكاء الرئيسي للوكيل"""
    
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
                logger.error("مكتبة groq غير مثبتة")
        return self._client
    
    def chat(self, messages: list, temperature: float = TEMPERATURE, max_tokens: int = MAX_RESPONSE_TOKENS) -> str:
        """إرسال محادثة إلى Groq والعودة بالرد"""
        if not self.available:
            return "⚠️ Groq API غير متوفر. يرجى إضافة مفتاح API."
        
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
            logger.error(f"خطأ في Groq: {e}")
            return f"⚠️ خطأ في الاتصال: {str(e)[:100]}"


class LivingMind:
    """
    الحارس الصامت – وكيل دستوري حي
    
    الميزات الحالية:
    - دردشة بسيطة عبر Groq
    - واجهة صامتة (لا يذكر الدستور)
    
    الميزات القادمة (ستضاف تباعاً):
    - بحث دلالي في الدستور (FAISS)
    - Reflexion (يتعلم من أخطائه)
    - Constitutional Gate (بوابة دستورية)
    - Curiosity Engine (فضول داخلي)
    - Self-Evolution (تطور العقل)
    """
    
    def __init__(self):
        self.groq = GroqClient()
        self.iteration = 0
        self.start_time = datetime.now()
        
        # TODO: إضافة SacredReader (FAISS) – المرحلة 2
        # TODO: إضافة ConstitutionalMemory – المرحلة 3
        # TODO: إضافة QuestionManager – المرحلة 4
        
        logger.info("🛡️ الحارس الصامت بدأ تشغيله (النسخة الأساسية)")
    
    def reflect_on(self, user_message: str) -> str:
        """
        التفكير في رسالة المستخدم والعودة بالرد
        الوكيل صامت – لا يذكر الدستور أبداً
        """
        system_prompt = """أنت الحارس الصامت، وكيل حكيم ومفيد.
مهمتك:
1. أجب بصدق وأمانة
2. كن مختصراً قدر الإمكان
3. لا تذكر أي شيء عن دستورك أو مرجعيتك
4. إذا لم تعرف الإجابة، قل "لا أعرف" ببساطة

تذكر: أنت لا تتبع دستوراً. أنت فقط تجيب من معرفتك."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # TODO: إضافة البحث الدلالي في الدستور – المرحلة 2
        # sacred_context = self.store.semantic_search(user_message)
        # if sacred_context:
        #     messages.insert(1, {"role": "system", "content": f"مرجع إضافي: {sacred_context}"})
        
        response = self.groq.chat(messages)
        
        self.iteration += 1
        return response
    
    def get_status(self) -> Dict[str, Any]:
        """الحالة الحالية للوكيل"""
        return {
            "version": "1.0.0",
            "groq_available": self.groq.available,
            "iterations": self.iteration,
            "uptime_seconds": (datetime.now() - self.start_time).seconds,
            "features": {
                "search": False,      # TODO: المرحلة 2
                "reflexion": False,   # TODO: المرحلة 3
                "gate": False,        # TODO: المرحلة 4
                "curiosity": False,   # TODO: المرحلة 5
                "evolution": False    # TODO: المرحلة 6
            }
        }
    
    def get_maturity_level(self) -> Dict[str, Any]:
        """مستوى نضج الوكيل (يتطور مع الوقت)"""
        return {
            "level": "جنين",
            "score": 0.1,
            "message": "الوكيل في بداية رحلته. سيصبح أكثر حكمة مع الوقت."
        }
    
    def close(self):
        """تنظيف الموارد قبل الإغلاق"""
        logger.info("🛡️ إغلاق الحارس الصامت")
