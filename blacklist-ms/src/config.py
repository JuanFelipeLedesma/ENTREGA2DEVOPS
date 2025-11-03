import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "change-me-very-strong")
PORT = int(os.getenv("PORT", "5000"))
