import os
import uuid
from pathlib import Path
from typing import Tuple, Optional
import logging
from pypdf import PdfReader

from app.config import PERSISTENT_DIR

logger = logging.getLogger(__name__)


class BookReader:
    def __init__(self):
        self.books_dir = Path(PERSISTENT_DIR) / "books"
        self.books_dir.mkdir(parents=True, exist_ok=True)

        self.current_book_text = ""
        self.current_book_name = ""
        self._chunks = []
        self._load_current_book()

    def _load_current_book(self):
        current_file = self.books_dir / "current_book.txt"
        if not current_file.exists():
            return

        with open(current_file, 'r', encoding='utf-8') as f:
            self.current_book_name = f.read().strip()

        book_path = self.books_dir / self.current_book_name
        if not book_path.exists():
            return

        try:
            with open(book_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.current_book_text = f.read()
            self._chunk_text()
            logger.info(f"✅ تم تحميل الكتاب: {self.current_book_name} ({len(self.current_book_text):,} حرفاً)")
        except Exception as e:
            logger.error(f"فشل تحميل الكتاب: {e}")

    def _chunk_text(self, chunk_size: int = 500):
        if not self.current_book_text:
            return
        words = self.current_book_text.split()
        self._chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            self._chunks.append(chunk)

    def get_random_chunk(self) -> Optional[str]:
        if not self._chunks:
            return None
        import random
        return random.choice(self._chunks)

    def search(self, keyword: str) -> Optional[str]:
        """بحث نصي بسيط في الكتاب المفتوح"""
        if not self._chunks:
            return None
        keyword_lower = keyword.lower()
        for chunk in self._chunks:
            if keyword_lower in chunk.lower():
                return chunk[:500]
        return None

    def load_book_from_pdf(self, filename: str, content: bytes) -> Tuple[bool, str]:
        try:
            temp_path = self.books_dir / f"temp_{uuid.uuid4().hex[:8]}.pdf"
            with open(temp_path, 'wb') as f:
                f.write(content)

            reader = PdfReader(temp_path)
            text_parts = []
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"[الصفحة {page_num}]\n{page_text}")
                except:
                    pass

            os.unlink(temp_path)

            if not text_parts:
                return False, "لم يتم استخراج أي نص من PDF"

            text = "\n\n".join(text_parts)
            txt_filename = filename.replace('.pdf', '.txt')
            txt_path = self.books_dir / txt_filename

            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)

            self.current_book_text = text
            self.current_book_name = txt_filename
            self._chunks = []
            self._chunk_text()

            with open(self.books_dir / "current_book.txt", 'w', encoding='utf-8') as f:
                f.write(txt_filename)

            return True, f"تم تحميل {len(text):,} حرفاً"
        except ImportError:
            return False, "مكتبة pypdf غير متوفرة"
        except Exception as e:
            return False, str(e)

    def load_book_from_txt(self, filename: str, content: bytes) -> Tuple[bool, str]:
        try:
            txt_path = self.books_dir / filename
            with open(txt_path, 'wb') as f:
                f.write(content)

            text_content = content.decode('utf-8', errors='ignore')
            self.current_book_text = text_content
            self.current_book_name = filename
            self._chunks = []
            self._chunk_text()

            with open(self.books_dir / "current_book.txt", 'w', encoding='utf-8') as f:
                f.write(filename)

            return True, f"تم تحميل {len(text_content):,} حرفاً"
        except Exception as e:
            return False, str(e)

    def get_current_book(self) -> str:
        return self.current_book_name if self.current_book_name else "لا يوجد كتاب مفتوح"

    @property
    def has_book(self) -> bool:
        return bool(self.current_book_text) and len(self.current_book_text) > 0

    @property
    def chunks(self):
        return self._chunks
