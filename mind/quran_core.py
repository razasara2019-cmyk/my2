"""
quran_core.py – النواة الدستورية للقرآن الكريم
الحارس الصامت يحرس هذا الدستور، ويعيشه، ولا يخرج عنه
الإصدار: 1.0 (6.0)
"""

import json
import logging
import os
import random
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class QuranCore:
    """
    النواة الدستورية الثابتة – القرآن الكريم
    هذا هو الدستور الذي يحرسه "الحارس الصامت"
    
    المبادئ:
    - القرآن ليس مصدراً خارجياً، بل هو هوية الكيان نفسه
    - لا يمكن تعديله أو تغييره
    - كل قرارات الكيان مستمدة منه
    """
    
    def __init__(self, quran_path: str = "quran.json"):
        """
        تهيئة النواة القرآنية
        
        المعاملات:
        - quran_path: المسار إلى ملف القرآن JSON
        """
        self.quran_path = quran_path
        self.surahs: List[Dict] = []
        self.verses: List[Dict] = []
        self._loaded = False
        self._load()
    
    def _load(self):
        """تحميل القرآن من الملف المحلي إلى الذاكرة"""
        if not os.path.exists(self.quran_path):
            logger.error(f"❌ ملف القرآن غير موجود: {self.quran_path}")
            logger.error("   قم بتشغيل: python download_quran.py")
            return
        
        try:
            with open(self.quran_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.surahs = data.get("surahs", [])
            
            # بناء قائمة مسطحة لكل الآيات للتسهيل
            for surah in self.surahs:
                surah_id = surah.get("id", 0)
                surah_name = surah.get("name", "")
                
                for verse in surah.get("verses", []):
                    self.verses.append({
                        "number": verse.get("number", 0),
                        "surah_id": surah_id,
                        "surah_name": surah_name,
                        "verse_id": verse.get("id", 0),
                        "text": verse.get("text", ""),
                        "juz": verse.get("juz", 0),
                        "page": verse.get("page", 0)
                    })
            
            self._loaded = True
            meta = data.get("meta", {})
            logger.info(f"🕋 تم تحميل القرآن الكريم: {len(self.surahs)} سورة، {len(self.verses)} آية")
            logger.info(f"   • المصدر: {meta.get('source', 'local')}")
            logger.info(f"   • الإصدار: {meta.get('version', '1.0')}")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ خطأ في قراءة JSON: {e}")
        except Exception as e:
            logger.error(f"❌ خطأ غير متوقع: {e}")
    
    def get_verse(self, surah_id: int, verse_id: int) -> Optional[str]:
        """
        استرجاع آية محددة
        
        المعاملات:
        - surah_id: رقم السورة (1-114)
        - verse_id: رقم الآية داخل السورة
        
        الإرجاع:
        - نص الآية أو None
        """
        for verse in self.verses:
            if verse["surah_id"] == surah_id and verse["verse_id"] == verse_id:
                return verse["text"]
        return None
    
    def get_verse_by_number(self, number: int) -> Optional[Dict]:
        """
        استرجاع آية برقمها المطلق (1-6236)
        
        المعاملات:
        - number: رقم الآية المطلق
        
        الإرجاع:
        - بيانات الآية أو None
        """
        for verse in self.verses:
            if verse["number"] == number:
                return verse.copy()
        return None
    
    def get_surah(self, surah_id: int) -> Optional[Dict]:
        """
        استرجاع سورة كاملة
        
        المعاملات:
        - surah_id: رقم السورة (1-114)
        
        الإرجاع:
        - بيانات السورة أو None
        """
        for surah in self.surahs:
            if surah.get("id") == surah_id:
                return surah.copy()
        return None
    
    def search_verses(self, keyword: str, top_k: int = 10) -> List[Dict]:
        """
        البحث عن آيات تحتوي على كلمة معينة
        
        المعاملات:
        - keyword: الكلمة المطلوب البحث عنها
        - top_k: عدد النتائج المطلوبة
        
        الإرجاع:
        - قائمة بالآيات التي تحتوي على الكلمة
        """
        if not keyword or not keyword.strip():
            return []
        
        keyword_lower = keyword.lower()
        results = []
        
        for verse in self.verses:
            if keyword_lower in verse["text"].lower():
                results.append(verse.copy())
        
        return results[:top_k]
    
    def get_random_verse(self) -> Optional[Dict]:
        """استرجاع آية عشوائية (للتأمل والتفكر)"""
        if not self.verses:
            return None
        return random.choice(self.verses).copy()
    
    def get_verses_by_juz(self, juz_number: int) -> List[Dict]:
        """
        استرجاع جميع آيات جزء معين
        
        المعاملات:
        - juz_number: رقم الجزء (1-30)
        
        الإرجاع:
        - قائمة بالآيات في هذا الجزء
        """
        return [v.copy() for v in self.verses if v.get("juz") == juz_number]
    
    def get_verses_by_page(self, page_number: int) -> List[Dict]:
        """
        استرجاع جميع آيات صفحة معينة
        
        المعاملات:
        - page_number: رقم الصفحة (1-604)
        
        الإرجاع:
        - قائمة بالآيات في هذه الصفحة
        """
        return [v.copy() for v in self.verses if v.get("page") == page_number]
    
    @property
    def is_loaded(self) -> bool:
        """هل تم تحميل القرآن بنجاح؟"""
        return self._loaded
    
    def get_stats(self) -> Dict[str, Any]:
        """إحصائيات النواة القرآنية"""
        return {
            "loaded": self._loaded,
            "surahs_count": len(self.surahs),
            "verses_count": len(self.verses),
            "source": self.quran_path
        }
    
    def get_summary(self) -> str:
        """ملخص عن القرآن الكريم"""
        return f"""🕋 القرآن الكريم – الدستور الأعلى
• {len(self.surahs)} سورة
• {len(self.verses)} آية
• المصدر: {self.quran_path}
• الحالة: {'✅ محمول' if self._loaded else '❌ غير محمول'}
"""
