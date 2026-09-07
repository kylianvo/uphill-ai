import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
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

    # Encrypts third-party OAuth tokens in athlete_connections. Generate with
    # services.token_crypto.generate_key(). Rotating it invalidates every stored
    # device-account token and forces all athletes to reconnect.
    TOKEN_ENCRYPTION_KEY: str = os.getenv("TOKEN_ENCRYPTION_KEY", "")

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

    # KB RAG engine — 'gemini' (default: distilled kb_chunks + Gemini) or 'notebooklm' (ad-hoc / distillation)
    RAG_ENGINE: str = os.getenv("RAG_ENGINE", "gemini")
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

    # COROS MCP integration. Obtain CLIENT_ID/SECRET once by running
    # scripts/register_coros_client.py (RFC 7591 dynamic client registration).
    COROS_CLIENT_ID: str = os.getenv("COROS_CLIENT_ID", "")
    COROS_CLIENT_SECRET: str = os.getenv("COROS_CLIENT_SECRET", "")
    COROS_REDIRECT_URI: str = os.getenv(
        "COROS_REDIRECT_URI", "https://api.uphill-ai.io.vn/api/integrations/coros/callback"
    )
    COROS_MCP_ENDPOINT: str = os.getenv("COROS_MCP_ENDPOINT", "https://mcp.coros.com/mcp")

    # Where the OAuth callback redirects the athlete's browser after a COROS
    # connect attempt (success or failure) -- the static-export frontend, not the API.
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://uphill-ai.io.vn")

    # Shadow mode records match decisions without marking workouts complete.
    # Keep this true until the assigner's thresholds have been calibrated
    # against real athlete data -- an uncalibrated matcher writing is_completed
    # would corrupt the training history it exists to describe.
    MATCHING_SHADOW_MODE: bool = os.getenv("MATCHING_SHADOW_MODE", "true").lower() != "false"

    # Require HttpOnly state cookie on COROS OAuth callback (RFC 6749 s10.12).
    # Enabled by default. In staging or cross-origin dev environments, browsers
    # drop third-party cookies on cross-origin fetch, so setting this to false
    # allows legitimate OAuth flows using state & PKCE verification.
    COROS_REQUIRE_STATE_COOKIE: bool = os.getenv("COROS_REQUIRE_STATE_COOKIE", "true").lower() != "false"


settings = Config()
