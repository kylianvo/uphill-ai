import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    API_PORT: int = int(os.getenv("PORT", "8000"))
    API_HOST: str = os.getenv("HOST", "0.0.0.0")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")

    # PostgreSQL connection URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://uphill:uphill_secret@localhost:5432/uphill_ai"
    )

    # JWT secret (generate a strong random key in production)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "uphill-ai-super-secret-dev-key-change-in-prod")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: list = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")

    # NotebookLM — system-level config (not per-user)
    NOTEBOOKLM_NOTEBOOK_ID: str = os.getenv("NOTEBOOKLM_NOTEBOOK_ID", "")
    NOTEBOOKLM_AUTH_JSON: str = os.getenv("NOTEBOOKLM_AUTH_JSON", "")

settings = Config()
