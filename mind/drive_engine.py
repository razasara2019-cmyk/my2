"""
drive_engine.py – محرك الدافع الداخلي للكيان الدستوري الحي
الإصدار: 1.0 (5.1.0)

هذا المحرك هو "قلب" الكيان. يعمل في الخلفية ويراقب الحالة الداخلية.
عندما تصل مشاعر الكيان (اليقين، الشك، التوتر، الفضول) إلى عتبات معينة،
يتحرك الكيان من تلقاء نفسه للتفكر أو البحث أو التأمل.
"""

import time
import threading
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class InternalDriveEngine:
    """
    محرك الدافع الداخلي – يجعل الكيان يتحرك من ذاته.
    
    يعمل في خيط منفصل ويراقب الحالة الداخلية (InternalState) بشكل دوري.
    عندما تتجاوز المقاييس العتبات المحددة، يُطلق دوافع (drives) مثل:
    - التفكر (reflection): عندما ينخفض اليقين أو يرتفع التوتر
    - الفضول (curiosity): عندما يرتفع الفضول
    - التأمل (contemplation): عندما يمر وقت طويل دون تفاعل
    """
    
    # العتبات الافتراضية
    DEFAULT_CERTAINTY_THRESHOLD = 0.4
    DEFAULT_DOUBT_THRESHOLD = 0.6
    DEFAULT_CURIOSITY_THRESHOLD = 0.7
    DEFAULT_TENSION_THRESHOLD = 0.5
    DEFAULT_IDLE_THRESHOLD = 3600  # 1 ساعة
    
    def __init__(self, internal_state, reflective_engine=None):
        self.state = internal_state
        self.reflective = reflective_engine
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # عتبات قابلة للتعديل
        self.certainty_threshold = self.DEFAULT_CERTAINTY_THRESHOLD
        self.doubt_threshold = self.DEFAULT_DOUBT_THRESHOLD
        self.curiosity_threshold = self.DEFAULT_CURIOSITY_THRESHOLD
        self.tension_threshold = self.DEFAULT_TENSION_THRESHOLD
        self.idle_threshold = self.DEFAULT_IDLE_THRESHOLD
        
        # سجل الدوافع
        self.drive_log: List[Dict] = []
        self._last_drive_time = 0
        self._cooldown_seconds = 60
        
        logger.info("🫀 InternalDriveEngine initialized (inactive)")
    
    def start(self):
        """بدء محرك الدافع الداخلي"""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("🫀 InternalDriveEngine started – الكيان يتحرك من ذاته")
    
    def stop(self):
        """إيقاف محرك الدافع الداخلي"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("🫀 InternalDriveEngine stopped")
    
    def _loop(self):
        """الحلقة الرئيسية – تعمل في الخلفية"""
        cycle = 0
        while self.running:
            try:
                self._check_and_drive()
                cycle += 1
                if cycle % 12 == 0:  # كل دقيقة تقريباً
                    self._adjust_thresholds()
            except Exception as e:
                logger.error(f"❌ Drive engine error: {e}")
            time.sleep(5)
    
    def _check_and_drive(self):
        """فحص الحالة وإطلاق الدافع المناسب"""
        now = time.time()
        
        if now - self._last_drive_time < self._cooldown_seconds:
            return
        
        drive_type = None
        reason = None
        
        # الأولوية للتوتر
        if self.state.internal_tension > self.tension_threshold:
            drive_type = "resolve_tension"
            reason = f"التوتر مرتفع: {self.state.internal_tension:.2f}"
            self.state.update_tension(-0.1)
        
        elif self.state.doubt > self.doubt_threshold:
            drive_type = "investigate"
            reason = f"الشك مرتفع: {self.state.doubt:.2f}"
        
        elif self.state.certainty < self.certainty_threshold:
            drive_type = "reinforce"
            reason = f"اليقين منخفض: {self.state.certainty:.2f}"
        
        elif self.state.curiosity > self.curiosity_threshold:
            drive_type = "explore"
            reason = f"الفضول مرتفع: {self.state.curiosity:.2f}"
        
        elif (now - self.state.last_interaction) > self.idle_threshold:
            drive_type = "contemplate"
            reason = f"خمول: {int((now - self.state.last_interaction)/60)} دقيقة"
        
        if drive_type:
            self._launch_drive(drive_type, reason)
            self._last_drive_time = now
    
    def _launch_drive(self, drive_type: str, reason: str):
        """إطلاق دافع داخلي"""
        with self._lock:
            logger.info(f"💭 [DRIVE] {drive_type}: {reason}")
            
            # تسجيل الدافع
            self.drive_log.append({
                "timestamp": time.time(),
                "type": drive_type,
                "reason": reason,
                "state": {
                    "certainty": self.state.certainty,
                    "doubt": self.state.doubt,
                    "curiosity": self.state.curiosity,
                    "tension": self.state.internal_tension,
                    "mood": self.state.mood
                }
            })
            
            if len(self.drive_log) > 50:
                self.drive_log.pop(0)
            
            self.state.record_reflection()
            
            if self.reflective:
                thread = threading.Thread(
                    target=self._run_reflection,
                    args=(drive_type, reason),
                    daemon=True
                )
                thread.start()
    
    def _run_reflection(self, drive_type: str, reason: str):
        """تشغيل التفكر"""
        try:
            mapping = {
                "resolve_tension": "resolve_contradiction",
                "investigate": "investigate",
                "reinforce": "reinforce",
                "explore": "seek_answers",
                "contemplate": "contemplative"
            }
            ref_type = mapping.get(drive_type)
            if ref_type and hasattr(self.reflective, 'reflect_on_demand'):
                self.reflective.reflect_on_demand(ref_type)
        except Exception as e:
            logger.error(f"❌ Reflection failed: {e}")
    
    def _adjust_thresholds(self):
        """تعديل العتبات تدريجياً (النضج)"""
        self.certainty_threshold = max(0.2, self.certainty_threshold - 0.001)
        self.doubt_threshold = min(0.9, self.doubt_threshold + 0.001)
        self.tension_threshold = max(0.3, self.tension_threshold - 0.001)
    
    def get_stats(self) -> Dict[str, Any]:
        """إحصائيات المحرك"""
        return {
            "running": self.running,
            "total_drives": len(self.drive_log),
            "last_drive": self.drive_log[-1] if self.drive_log else None,
            "thresholds": {
                "certainty": round(self.certainty_threshold, 3),
                "doubt": round(self.doubt_threshold, 3),
                "curiosity": round(self.curiosity_threshold, 3),
                "tension": round(self.tension_threshold, 3),
                "idle": self.idle_threshold
            },
            "cooldown_seconds": self._cooldown_seconds
        }
    
    def trigger_immediate_drive(self, drive_type: str):
        """إطلاق دافع فوري (للاختبار)"""
        self._launch_drive(drive_type, "manual trigger")
        self._last_drive_time = time.time()
