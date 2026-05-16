import os
import base64
import hashlib
import logging
from datetime import datetime
from pathlib import Path

from github import Github

from app.config import GITHUB_TOKEN, PERSISTENT_DIR

logger = logging.getLogger(__name__)

GITHUB_REPO = "sararazadz-prog/my"
GITHUB_BRANCH = "main"


def is_binary_file(file_path: str) -> bool:
    binary_extensions = ['.db', '.sqlite', '.sqlite3', '.pdf', '.zip']
    if any(file_path.endswith(ext) for ext in binary_extensions):
        return True
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
        return b'\x00' in chunk
    except:
        return True


def sync_to_github(local_path: str, repo_path: str, commit_message: str = None) -> bool:
    if not GITHUB_TOKEN:
        return False
    if not os.path.exists(local_path):
        return False
    if commit_message is None:
        commit_message = f"Backup: {datetime.now().isoformat()}"

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)

        with open(local_path, 'rb') as f:
            raw_bytes = f.read()

        if is_binary_file(local_path):
            content = base64.b64encode(raw_bytes).decode('utf-8')
        else:
            content = raw_bytes.decode('utf-8', errors='replace')

        try:
            contents = repo.get_contents(repo_path, ref=GITHUB_BRANCH)
            repo.update_file(contents.path, commit_message, content, contents.sha, branch=GITHUB_BRANCH)
        except:
            repo.create_file(repo_path, commit_message, content, branch=GITHUB_BRANCH)
        return True
    except Exception as e:
        logger.error(f"فشل رفع {repo_path}: {e}")
        return False


def sync_from_github(local_path: str, repo_path: str) -> bool:
    if not GITHUB_TOKEN:
        return False
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        contents = repo.get_contents(repo_path, ref=GITHUB_BRANCH)
        content_bytes = base64.b64decode(contents.content)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as f:
            f.write(content_bytes)
        return True
    except:
        return False


def backup_agent_state(event: str = "manual"):
    logger.info(f"بدء النسخ الاحتياطي (الحدث: {event})")

    files_to_backup = [
        (f"{PERSISTENT_DIR}/constitution.db", "data/constitution.db"),
        (f"{PERSISTENT_DIR}/pending_questions.json", "data/pending_questions.json"),
        (f"{PERSISTENT_DIR}/learning_log.json", "data/learning_log.json"),
    ]

    for local_path, repo_path in files_to_backup:
        if os.path.exists(local_path):
            sync_to_github(local_path, repo_path, f"Backup: {event}")

    # نسخ الكتب
    books_dir = f"{PERSISTENT_DIR}/books"
    if os.path.exists(books_dir):
        for book_file in os.listdir(books_dir):
            book_path = os.path.join(books_dir, book_file)
            if os.path.isfile(book_path):
                sync_to_github(book_path, f"data/books/{book_file}", f"Backup book: {book_file}")

    logger.info("تم النسخ الاحتياطي")


def restore_agent_state():
    logger.info("استعادة الذاكرة من GitHub...")

    files_to_restore = [
        (f"{PERSISTENT_DIR}/constitution.db", "data/constitution.db"),
        (f"{PERSISTENT_DIR}/pending_questions.json", "data/pending_questions.json"),
        (f"{PERSISTENT_DIR}/learning_log.json", "data/learning_log.json"),
    ]

    for local_path, repo_path in files_to_restore:
        sync_from_github(local_path, repo_path)

    # استعادة الكتب
    books_dir = f"{PERSISTENT_DIR}/books"
    os.makedirs(books_dir, exist_ok=True)
    # ملاحظة: استعادة الكbooks بشكل فردي يمكن إضافته لاحقاً
