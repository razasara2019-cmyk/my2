"""
internal_state.py – الحالة الداخلية الحقيقية للكيان
اليقين، الشك، الفضول، التوتر – نابعة من سلوكه الفعلي
"""

import time
from collections import deque
from typing import List, Dict, Any


class InternalState:
    """
    الحالة الداخلية للكيان الدستوري الحي
    هذه هي "مشاعر" الكيان الأولية
    """
    
    CERTAINTY_THRESHOLD = 0.4
    DOUBT_THRESHOLD = 0.6
    CURIOSITY_THRESHOLD = 0.7
    TENSION_THRESHOLD = 0.5
    IDLE_THRESHOLD = 3600
    
    def __init__(self):
        self.thought_history = deque(maxlen=100)
        self.reflection_times = deque(maxlen=20)
        self.pruning_times = deque(maxlen=10)
        self.internal_tension = 0.0
        self.curiosity_vector: List[str] = []
        self.last_interaction = time.time()
        self._certainty_threshold = self.CERTAINTY_THRESHOLD
        self._doubt_threshold = self.DOUBT_THRESHOLD
        self._curiosity_threshold = self.CURIOSITY_THRESHOLD
        self._tension_threshold = self.TENSION_THRESHOLD
    
    @property
    def certainty(self) -> float:
        if not self.thought_history:
            return 0.5
        recent = list(self.thought_history)[-20:]
        accepted = sum(1 for _, a in recent if a)
        return accepted / len(recent) if recent else 0.5
    
    @property
    def doubt(self) -> float:
        return 1.0 - self.certainty
    
    @property
    def curiosity(self) -> float:
        now = time.time()
        recent = sum(1 for t in self.reflection_times if now - t < 3600)
        return min(1.0, recent / 10.0)
    
    @property
    def mood(self) -> str:
        if self.internal_tension > 0.7:
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
    
    def record_thought(self, accepted: bool):
        self.thought_history.append((time.time(), accepted))
    
    def record_reflection(self):
        self.reflection_times.append(time.time())
    
    def record_pruning(self):
        self.pruning_times.append(time.time())
    
    def record_interaction(self):
        self.last_interaction = time.time()
    
    def update_tension(self, delta: float):
        self.internal_tension = max(0.0, min(1.0, self.internal_tension + delta))
    
    def adjust_thresholds(self, success_rate: float):
        if success_rate > 0.7:
            self._certainty_threshold = max(0.2, self._certainty_threshold - 0.02)
            self._doubt_threshold = min(0.9, self._doubt_threshold + 0.02)
            self._tension_threshold = max(0.3, self._tension_threshold - 0.02)
        elif success_rate < 0.3:
            self._certainty_threshold = min(0.6, self._certainty_threshold + 0.02)
            self._doubt_threshold = max(0.4, self._doubt_threshold - 0.02)
            self._tension_threshold = min(0.7, self._tension_threshold + 0.02)
    
    def get_full_state(self) -> Dict[str, Any]:
        return {
            "certainty": round(self.certainty, 3),
            "doubt": round(self.doubt, 3),
            "curiosity": round(self.curiosity, 3),
            "mood": self.mood,
            "tension": round(self.internal_tension, 3),
            "curiosity_topics": self.curiosity_vector[:5],
            "thresholds": {
                "certainty": round(self._certainty_threshold, 3),
                "doubt": round(self._doubt_threshold, 3),
                "curiosity": round(self._curiosity_threshold, 3),
                "tension": round(self._tension_threshold, 3),
            },
            "stats": {
                "total_thoughts": len(self.thought_history),
                "total_reflections": len(self.reflection_times),
                "last_interaction_seconds_ago": round(time.time() - self.last_interaction, 1)
            }
        }
