"""
الذاكرة الدلالية الحية – نسخة خفيفة جداً
لا تحتاج إلى torch أو chromadb أو sentence-transformers
تعمل مع LightEmbeddings فقط
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

try:
    from mind.light_embeddings import LightEmbeddings
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("LightEmbeddings غير متوفر، سيتم استخدام بحث نصي بسيط")


class GraphMind:
    def __init__(self):
        self.documents = []
        self.doc_ids = []
        self.metadata = {}
        
        if EMBEDDINGS_AVAILABLE:
            self.embeddings = LightEmbeddings()
            logger.info("✅ LightEmbeddings جاهز للعمل")
        else:
            self.embeddings = None
            logger.warning("⚠️ سيتم استخدام البحث النصي البسيط")
    
    def add_document(self, doc_id: str, text: str, meta: Dict = None):
        if not text or len(text.strip()) < 10:
            return False
            
        if doc_id not in self.doc_ids:
            self.doc_ids.append(doc_id)
            self.documents.append(text)
            self.metadata[doc_id] = meta or {}
            
            if self.embeddings:
                self.embeddings.add_documents([doc_id], [text])
            
            logger.info(f"📄 أضيف: {text[:50]}...")
            return True
        return False
    
    def search_semantic(self, query: str, top_k: int = 5) -> List[Dict]:
        if not query or not self.documents:
            return []
        
        if self.embeddings:
            results = self.embeddings.search(query, top_k)
            return [
                {
                    'id': r['id'],
                    'text': r['text'],
                    'score': r['score'],
                    'metadata': self.metadata.get(r['id'], {})
                }
                for r in results
            ]
        
        # بحث نصي بسيط (بديل طارئ)
        query_lower = query.lower()
        scores = []
        for i, doc in enumerate(self.documents):
            score = doc.lower().count(query_lower) / (len(doc) + 1)
            scores.append((i, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for i, score in scores[:top_k]:
            if score > 0:
                results.append({
                    'id': self.doc_ids[i],
                    'text': self.documents[i],
                    'score': score,
                    'metadata': self.metadata.get(self.doc_ids[i], {})
                })
        return results
    
    def get_all_documents(self) -> List[Dict]:
        return [
            {'id': doc_id, 'text': text, 'metadata': self.metadata.get(doc_id, {})}
            for doc_id, text in zip(self.doc_ids, self.documents)
        ]
    
    def get_stats(self) -> Dict:
        return {
            'total_documents': len(self.doc_ids),
            'embeddings_available': self.embeddings is not None
        }
    
    def clear(self):
        self.documents = []
        self.doc_ids = []
        self.metadata = {}
        if self.embeddings:
            self.embeddings = LightEmbeddings()
        logger.info("🗑️ تم مسح الذاكرة")
