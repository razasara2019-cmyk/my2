import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

PERSISTENT_DIR = os.environ.get("PERSISTENT_DIR", "/data")
BOOKS_DIR = f"{PERSISTENT_DIR}/books"

MAX_BOOK_SIZE = 10 * 1024 * 1024
MAX_RESPONSE_TOKENS = 800
TEMPERATURE = 0.7

CONSTITUTION_WEIGHT = 1.0
BOOK_WEIGHT = 0.3

QURAN_URL = "https://cdn.jsdelivr.net/npm/quran-json@3.1.2/dist/quran.json"
CONSTITUTION_FILE = f"{PERSISTENT_DIR}/constitution.txt"
DB_PATH = f"{PERSISTENT_DIR}/constitution.db"
PENDING_QUESTIONS_FILE = f"{PERSISTENT_DIR}/pending_questions.json"
LEARNING_LOG_FILE = f"{PERSISTENT_DIR}/learning_log.json"
