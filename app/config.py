import os
from pathlib import Path

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

BASE_DIR = Path(__file__).parent.parent
PERSISTENT_DIR = Path(os.environ.get("PERSISTENT_DIR", "/tmp/silent_guardian"))

MAX_RESPONSE_TOKENS = 800
TEMPERATURE = 0.7

QURAN_URL = "https://cdn.jsdelivr.net/npm/quran-json@3.1.2/dist/quran.json"
