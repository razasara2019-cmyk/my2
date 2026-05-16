import requests
import logging

logger = logging.getLogger(__name__)
QURAN_URL = "https://cdn.jsdelivr.net/npm/quran-json@3.1.2/dist/quran.json"


def load_quran():
    logger.info("تحميل القرآن...")
    response = requests.get(QURAN_URL, timeout=30)
    response.raise_for_status()
    quran_data = response.json()

    full_text = ""
    for sura in quran_data:
        for verse in sura["verses"]:
            full_text += verse["text"] + "\n"

    words = full_text.split()
    chunks = []
    chunk_size = 200
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))

    logger.info(f"تم تحميل {len(full_text):,} حرفاً، {len(chunks)} مقطعاً")
    return full_text, chunks
