"""
graph_mind.py – الذاكرة الدلالية للكيان الدستوري الحي
الإصدار: 5.0a (EmbedDB – نسخة آمنة للتشغيل الأول)
"""

import logging
from typing import List, Dict, Any, Optional

try:
    from embeddb import EmbedDB
    EMBEDDB_AVAILABLE = True
except ImportError:
    EMBEDDB_AVAILABLE = False
    raise ImportError("❌ embeddb غير مثبت. قم بتشغيل: pip install embeddb")

logger = logging.getLogger(__name__)


class GraphMind:
    
    def __init__(self, **kwargs):
        self.db = EmbedDB()
        self.doc_counter = 0
        logger.info("✅ GraphMind جاهز (الوضع: EmbedDB)")
    
    def add_document(self, text: str, metadata: Optional[Dict] = None) -> str:
        if not text or not text.strip():
            raise ValueError("لا يمكن إضافة نص فارغ")
        
        doc_id = f"doc_{self.doc_counter}"
        self.doc_counter += 1
        self.db.add_text(doc_id, text)
        
        logger.info(f"📄 أضيف: {text[:50]}...")
        return doc_id
    
    def search_semantic(self, query: str, top_k: int = 5) -> List[Dict]:
        if not query or not query.strip():
            return []
        
        results = self.db.search_text(query, top_k=top_k)
        return results
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        return self.search_semantic(query, top_k)
    
    def get_all_texts(self) -> List[str]:
        if hasattr(self.db, 'texts'):
            return [t["text"] for t in self.db.texts]
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_documents": self.doc_counter,
            "mode": "embeddb",
            "embeddb_available": EMBEDDB_AVAILABLE,
            "version": "5.0a"
        }
    
    def clear(self) -> None:
        self.db = EmbedDB()
        self.doc_counter = 0
        logger.info("🗑️ تم مسح الذاكرة")
    
    def get_document_count(self) -> int:
        return self.doc_counter
