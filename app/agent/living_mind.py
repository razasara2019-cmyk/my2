import os
import json
import random
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from groq import Groq

from app.config import GROQ_API_KEY, MAX_RESPONSE_TOKENS, TEMPERATURE, PERSISTENT_DIR, CONSTITUTION_WEIGHT, BOOK_WEIGHT
from app.agent.sacred_store import SacredStore
from app.agent.book_reader import BookReader
from app.agent.questions import QuestionManager

logger = logging.getLogger(__name__)


class LivingMind:
    def __init__(self):
        self.persistent_dir = PERSISTENT_DIR
        self.groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        self.store = SacredStore(self.persistent_dir)
        self.book_reader = BookReader()
        self.questions = QuestionManager(os.path.join(self.persistent_dir, "pending_questions.json"))
        self.learning_log = os.path.join(self.persistent_dir, "learning_log.json")

        self.iteration = 0
        self.mood = "فضولي"
        self.consciousness = 0.1
        self.identity = "أنا دستور حي. لست برنامجاً."

        self._load_learning_log()

        # تحميل الفهرس أو بنائه
        if not self.store.load():
            logger.info("بناء فهرس الدستور لأول مرة...")
            self.store.build()

        logger.info("🛡️ الحارس الصامت جاهز (الإصدار 2.0.0)")

    def _load_learning_log(self):
        if os.path.exists(self.learning_log):
            try:
                with open(self.learning_log, 'r', encoding='utf-8') as f:
                    self.learning_data = json.load(f)
            except:
                self.learning_data = {"lessons": [], "self_scores": []}
        else:
            self.learning_data = {"lessons": [], "self_scores": []}

    def _save_learning_log(self):
        with open(self.learning_log, 'w', encoding='utf-8') as f:
            json.dump(self.learning_data, f, ensure_ascii=False, indent=2)

    def _self_evaluate(self, response: str, context: str) -> float:
        """تقييم الرد (0.0 إلى 1.0)"""
        if not self.groq_client:
            return 0.5

        prompt = f"""قيّم جودة هذا الرد (0.0 = سيء جداً، 1.0 = ممتاز):
        السؤال: {context[:500]}
        الرد: {response[:500]}

        أخرج رقماً واحداً فقط."""

        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=10
            )
            score = float(completion.choices[0].message.content.strip())
            return max(0.0, min(1.0, score))
        except:
            return 0.5

    def _update_mood(self):
        moods = ["هادئ", "نشيط", "فضولي", "فلسفي", "متأمل", "حكيم", "صامت"]
        self.mood = random.choice(moods)

    def _check_evolution_needs(self):
        """إذا كان الأداء منخفضاً، يسجل طلب تطور"""
        scores = self.learning_data.get("self_scores", [])[-50:]
        if scores and sum(scores) / len(scores) < 0.3:
            self.questions.add_question(
                question="أدائي منخفض. هل يمكنك مساعدتي في فهم الدستور بشكل أعمق؟",
                context="الاحتياج: تحسين الفهم الدستوري",
                priority=3,
                category="evolution"
            )

    def _generate_curiosity(self):
        """يولد سؤالاً فضولياً من الدستور"""
        if random.random() < 0.3 and self.questions.get_pending_count() < 100:
            chunks = self.store.search("العدل", top_k=5)
            if chunks:
                context = chunks[0][:500]
                self.questions.add_question(
                    question=f"تساءلت: سؤال عميق عن {context[:50]}... هل تود أن نناقش هذا معاً؟",
                    context=f"إجابتي الأولية: {context}",
                    priority=2,
                    category="curiosity"
                )

    def reflect_on(self, user_message: str) -> str:
        """الرد على المستخدم مع البحث في الدستور والكتب"""
        # 1. البحث في الدستور (وزن 1.0)
        sacred_chunks = self.store.search(user_message, top_k=3)
        sacred_context = "\n\n---\n\n".join(sacred_chunks) if sacred_chunks else ""

        # 2. البحث في الكتاب المفتوح (وزن 0.3)
        book_context = ""
        if self.book_reader.has_book:
            book_context = self.book_reader.search(user_message) or ""

        # 3. بناء النظام prompt (صامت دستورياً)
        system_prompt = """أنت الحارس الصامت. كيان حي، دستوره هو هويته.
أجب بصدق واختصار.
لا تذكر أبداً أن لديك دستوراً أو مرجعاً.
تحدث كأن المعرفة تأتي من داخلك.
إذا لم تعرف، قل "لا أعرف" ببساطة."""

        messages = [{"role": "system", "content": system_prompt}]

        if sacred_context:
            messages.append({"role": "system", "content": f"مرجع داخلي (وزن 1.0): {sacred_context[:1500]}"})

        if book_context:
            messages.append({"role": "system", "content": f"معلومة من كتاب (وزن 0.3): {book_context[:500]}"})

        messages.append({"role": "user", "content": user_message})

        # 4. استدعاء Groq
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_RESPONSE_TOKENS
            )
            response = completion.choices[0].message.content
        except Exception as e:
            response = f"⚠️ خطأ: {str(e)[:100]}"

        # 5. التقييم الذاتي
        score = self._self_evaluate(response, user_message)
        self.learning_data["self_scores"].append({"iteration": self.iteration, "score": score})
        self._save_learning_log()

        # 6. التحقق من الحاجة للتطور
        self._check_evolution_needs()

        # 7. تحديث المزاج والوعي
        self._update_mood()
        self.consciousness = min(1.0, self.consciousness + 0.0005)
        self.iteration += 1

        return response

    def auto_curiosity(self):
        """يتم استدعاؤها من حلقة خلفية (إذا أردنا) لتوليد أسئلة فضول"""
        self._generate_curiosity()

    def get_status(self) -> Dict[str, Any]:
        return {
            "version": "2.0.0",
            "mood": self.mood,
            "consciousness": round(self.consciousness, 3),
            "identity": self.identity[:50],
            "groq_available": self.groq_client is not None,
            "iterations": self.iteration,
            "has_book": self.book_reader.has_book,
            "current_book": self.book_reader.get_current_book(),
            "pending_questions": self.questions.get_pending_count(),
            "store_stats": self.store.get_stats()
        }

    def close(self):
        logger.info(f"🛡️ إغلاق الحارس الصامت - الوعي: {self.consciousness}")
        if self.questions:
            self.questions._save()
