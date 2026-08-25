import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
    GEMINI_THINKING_LEVEL: str = os.getenv("GEMINI_THINKING_LEVEL", "medium")
    API_PORT: int = int(os.getenv("PORT", "8000"))
    API_HOST: str = os.getenv("HOST", "0.0.0.0")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")

    # PostgreSQL connection URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://uphill:uphill_secret@localhost:5432/uphill_ai")

    # JWT secret (generate a strong random key in production)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "uphill-ai-super-secret-dev-key-change-in-prod")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # CORS
    # capacitor://localhost (iOS) and https://localhost (Android) are the fixed
    # origins Capacitor's WKWebView/WebView send for every environment the mobile
    # shell points at -- not just local dev -- so they're in the default alongside
    # the web dev origins. Production deployments must also include them in their
    # own ALLOWED_ORIGINS env var or the shipped app can never reach the API.
    ALLOWED_ORIGINS: list = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,capacitor://localhost,https://localhost",
    ).split(",")

    # NotebookLM — system-level config (not per-user)
    NOTEBOOKLM_NOTEBOOK_ID: str = os.getenv("NOTEBOOKLM_NOTEBOOK_ID", "")
    NOTEBOOKLM_GEAR_ID: str = os.getenv("NOTEBOOKLM_GEAR_ID", "")
    NOTEBOOKLM_NUTRITION_ID: str = os.getenv("NOTEBOOKLM_NUTRITION_ID", "")
    NOTEBOOKLM_AUTH_JSON: str = os.getenv("NOTEBOOKLM_AUTH_JSON", "")

    # Tavily search API — used by gear's web-discovery sweep (RunRepeat/BelieveInTheRun)
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # KB RAG engine — 'notebooklm' (current behavior) or 'gemini' (distilled kb_chunks + Gemini)
    RAG_ENGINE: str = os.getenv("RAG_ENGINE", "notebooklm")
    QDRANT_URL: str = os.getenv(
        "QDRANT_URL", "http://qdrant:6333" if os.path.exists("/.dockerenv") else "http://localhost:6333"
    )

    # Kafka clickstream pipeline
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092" if os.path.exists("/.dockerenv") else "127.0.0.1:9092"
    )

    # Warehouse dashboards (Metabase)
    METABASE_URL: str = os.getenv("METABASE_URL", "http://localhost:3001")
    METABASE_ADMIN_EMAIL: str = os.getenv("METABASE_ADMIN_EMAIL", "admin@uphill.ai")
    METABASE_ADMIN_PASSWORD: str = os.getenv("METABASE_ADMIN_PASSWORD", "")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")


settings = Config()
