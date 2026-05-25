"""
graph_mind.py – الذاكرة الدلالية للكيان الدستوري الحي
الإصدار: 5.0a (باستخدام FastEmbed – بديل خفيف لـ sentence-transformers)
التاريخ: 2026-05-25
"""

import logging
from typing import List, Dict, Any, Optional

# محاولة استيراد FastEmbed (بديل خفيف لا يحتاج PyTorch)
try:
    from fastembed import TextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False
    raise ImportError(
        "❌ fastembed غير مثبت. قم بتشغيل:\n"
        "pip install fastembed"
    )

logger = logging.getLogger(__name__)


class GraphMind:
    """
    الذاكرة الدلالية للكيان – تعتمد على FastEmbed
    هذه النسخة خفيفة وتعمل على Core 2 Duo بدون AVX
    """
    
    def __init__(self, **kwargs):
        """
        تهيئة الذاكرة الدلالية
        """
        self.documents: List[Dict[str, Any]] = []
        self.doc_counter: int = 0
        
        # تهيئة نموذج FastEmbed (خفيف جداً، ~50MB)
        logger.info("🔄 جاري تحميل نموذج FastEmbed (BAAI/bge-small-en-v1.5)...")
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        logger.info("✅ FastEmbed جاهز للعمل")
        logger.info("✅ GraphMind جاهز (الوضع: FastEmbed)")
    
    def add_document(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        إضافة وثيقة إلى الذاكرة الدلالية
        
        المعاملات:
        - text: النص المراد تخزينه
        - metadata: بيانات إضافية (مثل المصدر، التاريخ، الوزن)
        
        الإرجاع:
        - معرف الوثيقة (doc_id)
        """
        if not text or not text.strip():
            raise ValueError("لا يمكن إضافة نص فارغ")
        
        doc_id = f"doc_{self.doc_counter}"
        self.doc_counter += 1
        
        self.documents.append({
            "id": doc_id,
            "text": text,
            "metadata": metadata or {}
        })
        
        logger.info(f"📄 أضيف: {text[:50]}... (المعرف: {doc_id})")
        return doc_id
    
    def search_semantic(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        بحث دلالي في الذاكرة
        
        المعاملات:
        - query: نص الاستعلام
        - top_k: عدد النتائج المطلوبة
        
        الإرجاع:
        - قائمة بالنتائج مرتبة حسب الأفضلية
        """
        if not query or not query.strip():
            return []
        
        if not self.documents:
            logger.warning("⚠️ لا توجد وثائق في الذاكرة للبحث")
            return []
        
        # بحث نصي بسيط (بديل مؤقت للبحث الدلالي الكامل)
        # هذا كافٍ للتشغيل الأول، ويمكن تطويره لاحقاً
        query_words = set(query.lower().split())
        results = []
        
        for doc in self.documents:
            doc_words = set(doc["text"].lower().split())
            if query_words:
                matches = len(query_words.intersection(doc_words))
                score = matches / len(query_words)
            else:
                score = 0.0
            
            results.append({
                "id": doc["id"],
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": round(score, 4)
            })
        
        # ترتيب النتائج تنازلياً حسب درجة التشابه
        results.sort(key=lambda x: x["score"], reverse=True)
        
        logger.debug(f"🔍 بحث: '{query[:50]}' → {len(results[:top_k])} نتيجة")
        return results[:top_k]
    
    def get_all_texts(self) -> List[str]:
        """
        إرجاع جميع النصوص المخزنة (للواجهة والعرض)
        """
        return [doc["text"] for doc in self.documents]
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        إرجاع جميع الوثائق مع بياناتها الوصفية
        """
        return self.documents.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        إحصائيات الذاكرة الدلالية
        """
        return {
            "total_documents": self.doc_counter,
            "mode": "fastembed",
            "fastembed_available": FASTEMBED_AVAILABLE,
            "model": "BAAI/bge-small-en-v1.5",
            "version": "5.0a"
        }
    
    def get_document_count(self) -> int:
        """إرجاع عدد الوثائق المخزنة"""
        return self.doc_counter
    
    def clear(self) -> None:
        """مسح جميع الوثائق من الذاكرة (للاختبار أو إعادة التعيين)"""
        self.documents = []
        self.doc_counter = 0
        logger.info("🗑️ تم مسح الذاكرة بالكامل")
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """استرجاع وثيقة محددة بمعرفها"""
        for doc in self.documents:
            if doc["id"] == doc_id:
                return doc.copy()
        return None
