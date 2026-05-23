"""
نموذج تضمين خفيف جداً – لا يحتاج إلى torch أو transformers
يستخدم scikit-learn و numpy فقط
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


class LightEmbeddings:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=384, stop_words=None)
        self.doc_vectors = None
        self.doc_ids = []
        self.doc_texts = []
        self.is_fitted = False
    
    def add_documents(self, doc_ids, texts):
        """إضافة وثائق جديدة إلى الذاكرة"""
        if not texts:
            return
        
        self.doc_ids.extend(doc_ids)
        self.doc_texts.extend(texts)
        
        if not self.is_fitted:
            self.doc_vectors = self.vectorizer.fit_transform(texts)
            self.is_fitted = True
        else:
            new_vectors = self.vectorizer.transform(texts)
            self.doc_vectors = np.vstack([self.doc_vectors.toarray(), new_vectors.toarray()])
    
    def search(self, query, top_k=5):
        """البحث عن الوثائق الأكثر تشابهاً مع الاستعلام"""
        if not self.is_fitted or self.doc_vectors is None:
            return []
        
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.doc_vectors).flatten()
        
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                results.append({
                    'id': self.doc_ids[idx],
                    'text': self.doc_texts[idx],
                    'score': float(similarities[idx])
                })
        return results
    
    def get_stats(self):
        return {
            'total_documents': len(self.doc_ids),
            'is_fitted': self.is_fitted,
            'vocabulary_size': len(self.vectorizer.vocabulary_) if self.is_fitted else 0
        }
