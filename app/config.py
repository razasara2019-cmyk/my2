import os
from pathlib import Path

# === البيئة ===
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# === المسارات ===
BASE_DIR = Path(__file__).parent.parent
PERSISTENT_DIR = Path(os.environ.get("PERSISTENT_DIR", "/tmp/silent_guardian"))

# === حدود الأداء ===
MAX_RESPONSE_TOKENS = 800
TEMPERATURE = 0.7

# === الدستور ===
QURAN_URL = "https://cdn.jsdelivr.net/npm/quran-json@3.1.2/dist/quran.json"
