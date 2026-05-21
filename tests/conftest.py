import os
import sys

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db"
)
os.environ.setdefault("JWT_SECRET", "secret")
os.environ.setdefault("SECRET_KEY", "secret")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_PASSWORD", "Password123!")
os.environ.setdefault("ADMIN_PHONE_NUMBER", "+79990001122")
os.environ.setdefault("ADMIN_FIRST_NAME", "Admin")
os.environ.setdefault("ADMIN_LAST_NAME", "User")
