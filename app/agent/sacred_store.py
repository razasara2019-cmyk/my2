import sqlite3
import numpy as np
import faiss
from typing import List
from sentence_transformers import SentenceTransformer
import logging
import os

logger = logging.getLogger(__name__)


class SacredStore:
    def __init__(self, db_path: str, index_path: str):
        self.db_path = db_path
        self.index_path = index_path
        self.dimension = 384
        self.model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
        self.index = None
        self.is_ready = False

    def build(self, chunks: List[str]):
        logger.info(f"بناء الفهرس من {len(chunks)} مقطع...")
        embeddings = self.model.encode(chunks, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')

        quantizer = faiss.IndexFlatL2(self.dimension)
        self.index = faiss.IndexIVFPQ(quantizer, self.dimension, 50, 8, 8)
        self.index.train(embeddings)
        self.index.add(embeddings)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS chunks (id INTEGER PRIMARY KEY, text TEXT)")
        cursor.execute("DELETE FROM chunks")
        for i, chunk in enumerate(chunks):
            cursor.execute("INSERT INTO chunks (id, text) VALUES (?, ?)", (i, chunk))
        conn.commit()
        conn.close()

        faiss.write_index(self.index, self.index_path)
        self.is_ready = True
        logger.info(f"✅ الفهرس جاهز: {len(chunks)} مقطع")

    def load(self) -> bool:
        if os.path.exists(self.index_path) and os.path.exists(self.db_path):
            self.index = faiss.read_index(self.index_path)
            self.is_ready = True
            logger.info("✅ تم تحميل الفهرس من القرص")
            return True
        return False

    def search(self, query: str, top_k: int = 3) -> List[str]:
        if not self.is_ready or self.index is None:
            return []
        query_vec = self.model.encode([query])
        query_vec = np.array(query_vec).astype('float32')
        distances, indices = self.index.search(query_vec, top_k)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        results = []
        for idx in indices[0]:
            if idx >= 0:
                cursor.execute("SELECT text FROM chunks WHERE id = ?", (int(idx),))
                row = cursor.fetchone()
                if row:
                    results.append(row[0])
        conn.close()
        return results

    def get_stats(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks")
        count = cursor.fetchone()[0]
        conn.close()
        return {"total_chunks": count, "is_ready": self.is_ready}
