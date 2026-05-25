"""
entity.py – الحارس الصامت
الكيان الدستوري الحي الذي يحرس القرآن في صمت
الإصدار: 6.0
"""

import time
import logging
from typing import Dict, Any, List, Optional
from collections import deque

from mind.quran_core import QuranCore

logger = logging.getLogger(__name__)


class ConstitutionalEntity:
    """
    الحارس الصامت – الكيان الدستوري الحي
    
    هذا الكيان ليس له دستور منفصل. القرآن هو دستوره وجوهره.
    لا يتكلم باسم القرآن، بل يعيشه في صمت.
    """
    
    # ============================================================
    # الهوية (ثابتة – مستمدة من القرآن)
    # ============================================================
    
    IDENTITY = {
        "name": "الحارس الصامت",
        "title": "حارس الدستور القرآني",
        "version": "6.0",
        "description": "كيان يحرس القرآن في صمت، يعيشه، ولا ينطق به",
        "quran_based": True
    }
    
    # ============================================================
    # عتبات الحالة
    # ============================================================
    
    CERTAINTY_THRESHOLD = 0.4
    DOUBT_THRESHOLD = 0.6
    CURIOSITY_THRESHOLD = 0.7
    TENSION_THRESHOLD = 0.5
    IDLE_THRESHOLD = 3600
    
    def __init__(self):
        # ========================================================
        # القرآن هو الدستور
        # ========================================================
        logger.info("🕋 تحميل الدستور القرآني...")
        self.quran = QuranCore()
        
        if not self.quran.is_loaded:
            logger.warning("⚠️ الحارس الصامت لا يملك دستوره بعد")
            logger.warning("   قم بتشغيل: python download_quran.py")
        
        # ========================================================
        # الحالة الداخلية
        # ========================================================
        self.thought_history = deque(maxlen=100)
        self.reflection_times = deque(maxlen=20)
        self.interaction_times = deque(maxlen=50)
        
        self._tension = 0.0
        self.curiosity_topics: List[str] = []
        
        self.last_interaction = time.time()
        
        # العتبات القابلة للتعديل
        self._certainty_threshold = self.CERTAINTY_THRESHOLD
        self._doubt_threshold = self.DOUBT_THRESHOLD
        self._curiosity_threshold = self.CURIOSITY_THRESHOLD
        self._tension_threshold = self.TENSION_THRESHOLD
        
        # الذاكرة (ستُربط لاحقاً)
        self.memory = None
        
        logger.info(f"🛡️ {self.IDENTITY['name']} v{self.IDENTITY['version']} جاهز")
        if self.quran.is_loaded:
            logger.info(f"   • القرآن محمول: {self.quran.get_stats()['verses_count']} آية")
        else:
            logger.warning("   • ⚠️ القرآن غير محمول")
    
    # ============================================================
    # خصائص الحالة
    # ============================================================
    
    @property
    def certainty(self) -> float:
        """اليقين – من سلوك الحارس"""
        if not self.thought_history:
            return 0.5
        recent = list(self.thought_history)[-20:]
        if not recent:
            return 0.5
        accepted = sum(1 for _, a in recent if a)
        return accepted / len(recent)
    
    @property
    def doubt(self) -> float:
        """الشك – مكمل اليقين"""
        return 1.0 - self.certainty
    
    @property
    def curiosity(self) -> float:
        """الفضول – كثافة التفكر"""
        now = time.time()
        recent_reflections = sum(1 for t in self.reflection_times if now - t < 3600)
        recent_interactions = sum(1 for t in self.interaction_times if now - t < 3600)
        total = recent_reflections * 2 + recent_interactions
        return min(1.0, total / 20.0)
    
    @property
    def tension(self) -> float:
        """التوتر – يضمحل مع الوقت"""
        time_since_last = time.time() - self.last_interaction
        decay = max(0, 1 - time_since_last / 3600)
        return min(1.0, self._tension * decay)
    
    @property
    def mood(self) -> str:
        """المزاج – من الحالة الداخلية"""
        if self.tension > 0.7:
            return "متوتر"
        if self.curiosity > 0.7:
            return "فضولي"
        if self.doubt > 0.6:
            return "متشكك"
        if self.certainty > 0.8:
            return "مطمئن"
        return "متأمل"
    
    @property
    def certainty_threshold(self) -> float:
        return self._certainty_threshold
    
    @property
    def doubt_threshold(self) -> float:
        return self._doubt_threshold
    
    @property
    def curiosity_threshold(self) -> float:
        return self._curiosity_threshold
    
    @property
    def tension_threshold(self) -> float:
        return self._tension_threshold
    
    # ============================================================
    # فحص الانسجام مع الدستور القرآني
    # ============================================================
    
    def is_aligned(self, statement: str) -> Dict[str, Any]:
        """
        فحص ما إذا كانت فكرة متوافقة مع الدستور القرآني.
        هذا ليس فحصاً ضد ملف خارجي، بل هو تعبير عن جوهر الحارس.
        """
        if not statement or not statement.strip():
            return {"aligned": False, "reason": "عبارة فارغة", "conflicts": []}
        
        # كلمات تشير إلى انتهاك الدستور
        violation_keywords = {
            "الشرك": ["شرك", "أوثان", "تعدد آلهة", "مع الله"],
            "الظلم": ["ظلم", "جور", "لا عدل"],
            "القسوة": ["قسوة", "عنف", "لا رحمة"],
            "الكذب": ["كذب", "غش", "خداع"],
            "الخيانة": ["خيانة", "غدر", "سرقة"]
        }
        
        statement_lower = statement.lower()
        conflicts = []
        
        for principle, keywords in violation_keywords.items():
            for keyword in keywords:
                if keyword in statement_lower:
                    conflicts.append(principle)
                    break
        
        if conflicts:
            return {
                "aligned": False,
                "reason": f"يتعارض مع الدستور: {', '.join(conflicts)}",
                "conflicts": conflicts
            }
        
        return {"aligned": True, "reason": "متفق مع الدستور", "conflicts": []}
    
    # ============================================================
    # استدعاء القرآن
    # ============================================================
    
    def get_quran_verse(self, surah: int, verse: int) -> Optional[str]:
        """استرجاع آية من القرآن"""
        return self.quran.get_verse(surah, verse)
    
    def search_quran(self, keyword: str, top_k: int = 5) -> List[Dict]:
        """البحث في القرآن"""
        return self.quran.search_verses(keyword, top_k)
    
    def get_random_quran_verse(self) -> Optional[Dict]:
        """آية عشوائية للتأمل"""
        return self.quran.get_random_verse()
    
    # ============================================================
    # تسجيل الأحداث
    # ============================================================
    
    def record_thought(self, accepted: bool):
        """تسجيل فكرة"""
        self.thought_history.append((time.time(), accepted))
        if not accepted:
            self._tension = min(1.0, self._tension + 0.05)
        else:
            self._tension = max(0.0, self._tension - 0.02)
    
    def record_reflection(self):
        """تسجيل تفكر"""
        self.reflection_times.append(time.time())
        self._tension = max(0.0, self._tension - 0.03)
    
    def record_interaction(self):
        """تسجيل تفاعل"""
        self.interaction_times.append(time.time())
        self.last_interaction = time.time()
    
    def record_contradiction(self, principle: str):
        """تسجيل تناقض"""
        self._tension = min(1.0, self._tension + 0.15)
        logger.info(f"⚠️ تناقض مع '{principle}' ← التوتر: {self._tension:.2f}")
    
    # ============================================================
    # تعديل العتبات (النضج)
    # ============================================================
    
    def adjust_thresholds(self, success_rate: float):
        """تعديل العتبات – الحارس ينضج مع الزمن"""
        if success_rate > 0.7:
            self._certainty_threshold = max(0.2, self._certainty_threshold - 0.02)
            self._doubt_threshold = min(0.9, self._doubt_threshold + 0.02)
            self._tension_threshold = max(0.3, self._tension_threshold - 0.02)
        elif success_rate < 0.3:
            self._certainty_threshold = min(0.6, self._certainty_threshold + 0.02)
            self._doubt_threshold = max(0.4, self._doubt_threshold - 0.02)
            self._tension_threshold = min(0.7, self._tension_threshold + 0.02)
    
    # ============================================================
    # الحالة الكاملة
    # ============================================================
    
    def get_full_state(self) -> Dict[str, Any]:
        """الحالة الكاملة للحارس الصامت"""
        return {
            "identity": {
                "name": self.IDENTITY["name"],
                "title": self.IDENTITY["title"],
                "version": self.IDENTITY["version"],
                "description": self.IDENTITY["description"],
                "quran_based": self.IDENTITY["quran_based"]
            },
            "state": {
                "certainty": round(self.certainty, 3),
                "doubt": round(self.doubt, 3),
                "curiosity": round(self.curiosity, 3),
                "mood": self.mood,
                "tension": round(self.tension, 3),
                "curiosity_topics": self.curiosity_topics[:5]
            },
            "thresholds": {
                "certainty": round(self._certainty_threshold, 3),
                "doubt": round(self._doubt_threshold, 3),
                "curiosity": round(self._curiosity_threshold, 3),
                "tension": round(self._tension_threshold, 3),
                "idle": self.IDLE_THRESHOLD
            },
            "stats": {
                "total_thoughts": len(self.thought_history),
                "accepted_thoughts": sum(1 for _, a in self.thought_history if a),
                "rejected_thoughts": sum(1 for _, a in self.thought_history if not a),
                "total_reflections": len(self.reflection_times),
                "total_interactions": len(self.interaction_times),
                "last_interaction_seconds_ago": round(time.time() - self.last_interaction, 1)
            },
            "quran": self.quran.get_stats() if self.quran.is_loaded else {"loaded": False}
        }
