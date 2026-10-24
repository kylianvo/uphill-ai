import json
import logging
import math
import os
from datetime import date

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_LLM_PRICES_USD_PER_M = {
    "gemini-3.8-flash": [
        {"until": "2026-12-31", "input": 0.75, "cached_input": 0.075, "output": 3.75},
        {"from": "2027-01-01", "input": 1.50, "cached_input": 0.15, "output": 7.50},
    ],
    # prompts up to 100K tokens; plan prompts stay well below
    "claude-haiku-5-5": [{"input": 0.10, "cached_input": 0.01, "output": 0.50}],
    # Optional coach chat override (CLAUDE_COACH_MODEL); prices for prompts up to the standard context.
    "claude-sonnet-5-5": [{"input": 2.00, "cached_input": 0.20, "output": 10.00}],
}


def _valid_price_rate(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def _valid_price_table(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    for model, windows in value.items():
        if not isinstance(model, str) or not model or not isinstance(windows, list):
            return False
        bounds = []
        for window in windows:
            if not isinstance(window, dict):
                return False
            if not all(_valid_price_rate(window.get(key)) for key in ("input", "cached_input", "output")):
                return False
            parsed_boundaries = {}
            for boundary in ("from", "until"):
                if boundary in window:
                    try:
                        parsed_boundaries[boundary] = date.fromisoformat(window[boundary])
                    except (TypeError, ValueError):
                        return False
            starts = parsed_boundaries.get("from", date.min)
            ends = parsed_boundaries.get("until", date.max)
            if starts > ends:
                return False
            bounds.append((starts, ends))
        bounds.sort()
        if any(starts <= previous_ends for (_, previous_ends), (starts, _) in zip(bounds, bounds[1:])):
            return False
    return True


def _parse_llm_prices(raw: str | None) -> dict:
    if raw is None or not raw.strip():
        return DEFAULT_LLM_PRICES_USD_PER_M
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        parsed = None
    if _valid_price_table(parsed):
        return parsed
    logger.warning("invalid LLM_PRICES_JSON; using verified defaults")
    return DEFAULT_LLM_PRICES_USD_PER_M


class Config:
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    GEMINI_THINKING_LEVEL: str = os.getenv("GEMINI_THINKING_LEVEL", "low")
    # Plan generation only: gemini | claude. Everything else stays on Gemini.
    PLAN_LLM_PROVIDER: str = os.getenv("PLAN_LLM_PROVIDER", "gemini")
    # low beat medium on quality and halved latency (docs/superpowers/haiku-latency/results.md)
    PLAN_LLM_EFFORT: str = os.getenv("PLAN_LLM_EFFORT", "low")
    PLAN_LLM_THINKING: str = os.getenv("PLAN_LLM_THINKING", "adaptive")  # adaptive | disabled
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_PLAN_MODEL: str = os.getenv("CLAUDE_PLAN_MODEL", "claude-haiku-5-5")
    # One-shot features moved off Gemini (services/claude_llm.py); each has its own provider flag below.
    CLAUDE_TEXT_MODEL: str = os.getenv("CLAUDE_TEXT_MODEL", "claude-haiku-5-5")
    CLAUDE_TEXT_EFFORT: str = os.getenv("CLAUDE_TEXT_EFFORT", "low")
    GEAR_LLM_PROVIDER: str = os.getenv("GEAR_LLM_PROVIDER", "gemini")
    NUTRITION_LLM_PROVIDER: str = os.getenv("NUTRITION_LLM_PROVIDER", "gemini")
    GOAL_JUDGE_LLM_PROVIDER: str = os.getenv("GOAL_JUDGE_LLM_PROVIDER", "gemini")
    WEEK_BRIEF_LLM_PROVIDER: str = os.getenv("WEEK_BRIEF_LLM_PROVIDER", "gemini")
    COACH_NUDGE_LLM_PROVIDER: str = os.getenv("COACH_NUDGE_LLM_PROVIDER", "gemini")
    LLM_JUDGE_PROVIDER: str = os.getenv("LLM_JUDGE_PROVIDER", "gemini")
    KNOWLEDGE_LLM_PROVIDER: str = os.getenv("KNOWLEDGE_LLM_PROVIDER", "gemini")
    KB_DISTILL_LLM_PROVIDER: str = os.getenv("KB_DISTILL_LLM_PROVIDER", "gemini")
    COACH_COPILOT_LLM_PROVIDER: str = os.getenv("COACH_COPILOT_LLM_PROVIDER", "gemini")
    COACH_CHAT_LLM_PROVIDER: str = os.getenv("COACH_CHAT_LLM_PROVIDER", "gemini")
    CLAUDE_COACH_MODEL: str = os.getenv("CLAUDE_COACH_MODEL", "claude-haiku-5-5")
    CLAUDE_COACH_EFFORT: str = os.getenv("CLAUDE_COACH_EFFORT", "low")
    CLAUDE_COACH_THINKING: str = os.getenv("CLAUDE_COACH_THINKING", "adaptive")  # adaptive | disabled
    API_PORT: int = int(os.getenv("PORT", "8000"))
    API_HOST: str = os.getenv("HOST", "0.0.0.0")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    # Outbound email (password reset codes). Empty SMTP_HOST = log and skip sending.
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "")
    # Public OAuth IDs for the web/Android and native iOS clients.
    GOOGLE_CLIENT_IDS: list[str] = [
        c.strip()
        for c in os.getenv(
            "GOOGLE_CLIENT_IDS",
            "451637841654-0eoo8qsa5fgnpm4cq0br8phgkhh92c5a.apps.googleusercontent.com,"
            "451637841654-ncj3jhv24t9rq665noctori05faajiej.apps.googleusercontent.com",
        ).split(",")
        if c.strip()
    ]
    APPLE_AUDIENCES: list[str] = [
        c.strip() for c in os.getenv("APPLE_AUDIENCES", "uphill.ai.app,ai.uphill.app").split(",") if c.strip()
    ]

    # PostgreSQL connection URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://uphill:uphill_secret@localhost:5432/uphill_ai")

    # JWT secret (generate a strong random key in production)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "uphill-ai-super-secret-dev-key-change-in-prod")
    JWT_ALGORITHM: str = "HS256"
    # Session lifetime. Sliding: every use past the halfway point pushes
    # expiry back out to the full window (db.verify_session), so an athlete
    # who opens the app at least once per window never has to log in again.
    JWT_EXPIRE_DAYS: int = int(os.getenv("JWT_EXPIRE_DAYS", "30"))

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
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:18080,http://127.0.0.1:18080,capacitor://localhost,https://localhost",
    ).split(",")

    # NotebookLM — read ONLY by backend/scripts/distill_principles.py, the operator
    # script that re-sweeps curated doctrine into kb_seed. No request path touches these:
    # the app serves every AI feature from the distilled KB via Gemini. Unset in normal
    # deployments; set them only when running that script.
    NOTEBOOKLM_NOTEBOOK_ID: str = os.getenv("NOTEBOOKLM_NOTEBOOK_ID", "")
    NOTEBOOKLM_NUTRITION_ID: str = os.getenv("NOTEBOOKLM_NUTRITION_ID", "")
    NOTEBOOKLM_AUTH_JSON: str = os.getenv("NOTEBOOKLM_AUTH_JSON", "")

    # Tavily search API — used by gear's web-discovery sweep (RunRepeat/BelieveInTheRun)
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    RACE_HISTORY_UTMB_ENABLED: bool = os.getenv("RACE_HISTORY_UTMB_ENABLED", "true").lower() == "true"
    RACE_HISTORY_VBM_ENABLED: bool = os.getenv("RACE_HISTORY_VBM_ENABLED", "true").lower() == "true"
    # Background thread that syncs pending claims and runs the weekly refresh;
    # off in tests so it does not race the test database.
    RACE_HISTORY_WORKER_ENABLED: bool = os.getenv("RACE_HISTORY_WORKER_ENABLED", "true").lower() == "true"
    # LLM goal judge (services/goal_judge.py). Off = deterministic A/B/C from the
    # anchors, same API and UI. Enable once golden_eval --service goal passes.
    GOAL_LLM_ENABLED: bool = os.getenv("GOAL_LLM_ENABLED", "false").lower() == "true"
    # Structural lint + race-readiness check on every generated week (services/plan_lint.py,
    # services/race_readiness.py). PLAN_LINT_RETRY adds one corrective regeneration when a week
    # breaks a rule. Off in tests (it reads the plan's earlier weeks from the DB).
    PLAN_LINT_ENABLED: bool = os.getenv("PLAN_LINT_ENABLED", "true").lower() == "true"
    PLAN_LINT_RETRY: bool = os.getenv("PLAN_LINT_RETRY", "true").lower() == "true"
    # Derive the goal's physical demands (services/goal_demands.py) and put them in the generation
    # prompt, the specificity lint and the fallback's volume ramp. Off in tests unless a test enables it.
    PLAN_DEMANDS_ENABLED: bool = os.getenv("PLAN_DEMANDS_ENABLED", "true").lower() == "true"
    # Assess a new plan's goal in a background thread at creation; off in tests
    # so the thread can't outlive a test and write into the next one's data.
    GOAL_ASSESS_ON_PLAN_CREATE: bool = os.getenv("GOAL_ASSESS_ON_PLAN_CREATE", "true").lower() == "true"
    RACE_HISTORY_WEEKLY_REFRESH_ENABLED: bool = (
        os.getenv("RACE_HISTORY_WEEKLY_REFRESH_ENABLED", "false").lower() == "true"
    )

    QDRANT_URL: str = os.getenv(
        "QDRANT_URL", "http://qdrant:6333" if os.path.exists("/.dockerenv") else "http://localhost:6333"
    )

    # Single source of truth for training block size (weeks per block), used by
    # plan generation, the 70% completion gate, and block review/evaluation.
    # See db.py's week_range_for_block/block_number_for_week helpers.
    #
    # Changed from 2 to 1 in 2026-09: plans/block_reviews rows created under the
    # old 2-week math keep their stored block_number, which is now reinterpreted
    # under 1-week windows (old block N = weeks 2N-1..2N is now read as block N =
    # week N). This was a deliberate, accepted cutover -- not a migration -- since
    # a majority of active plans already had 2nd-block history. See PR description.
    TAPER_BY_RULES: bool = True  # taper weeks are built by the rules from the plan's real peak, not by the model
    WEEKS_PER_BLOCK: int = 1

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
    COROS_DAILY_PUSH_LIMIT: int = int(os.getenv("COROS_DAILY_PUSH_LIMIT", "10"))
    # Garmin Connect Developer Program (Starter tier: push delivery only). Off until Garmin's
    # production review passes. The webhook URL registered in Garmin's API Tools carries
    # GARMIN_WEBHOOK_TOKEN as its last path segment.
    GARMIN_ENABLED: bool = os.getenv("GARMIN_ENABLED", "false").lower() == "true"
    GARMIN_CLIENT_ID: str = os.getenv("GARMIN_CLIENT_ID", "")
    GARMIN_CLIENT_SECRET: str = os.getenv("GARMIN_CLIENT_SECRET", "")
    GARMIN_REDIRECT_URI: str = os.getenv(
        "GARMIN_REDIRECT_URI", "https://api.uphill-ai.io.vn/api/integrations/garmin/callback"
    )
    GARMIN_WEBHOOK_TOKEN: str = os.getenv("GARMIN_WEBHOOK_TOKEN", "")
    # Hides Apple Health in the app (via /api/integrations/status) and 404s its sync
    # endpoint, without an app release.
    APPLE_HEALTH_ENABLED: bool = os.getenv("APPLE_HEALTH_ENABLED", "true").lower() != "false"
    # Resting HR, HRV and sleep riding on the Apple Health sync. Off: the server ignores
    # them and /status tells the app to stop reading them.
    APPLE_HEALTH_RECOVERY_ENABLED: bool = os.getenv("APPLE_HEALTH_RECOVERY_ENABLED", "true").lower() != "false"

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

    # LLM observability (services/observability.py). Empty keys disable Langfuse;
    # the Prometheus llm_* token/cost counters work regardless.
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    # EU region. Self-hosting Langfuse later changes only this value.
    LANGFUSE_BASE_URL: str = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
    LANGFUSE_ENVIRONMENT: str = os.getenv("LANGFUSE_ENVIRONMENT", os.getenv("ENVIRONMENT", "development"))
    LANGFUSE_SAMPLE_RATE: float = float(os.getenv("LANGFUSE_SAMPLE_RATE", "1.0"))
    # Seconds; bounds background export and shutdown flush only, never a request.
    LANGFUSE_TIMEOUT: int = int(os.getenv("LANGFUSE_TIMEOUT", "5"))
    # Git SHA of the deployed build, tagged on every trace so monitoring can compare releases.
    LANGFUSE_RELEASE: str = os.getenv("LANGFUSE_RELEASE", "")
    # Share of finished coach turns graded in-process by services/llm_judge.py (one extra
    # Gemini call each). Only the scores reach Langfuse. 0 disables.
    LLM_JUDGE_SAMPLE_RATE: float = float(os.getenv("LLM_JUDGE_SAMPLE_RATE", "0.1"))
    # Must stay false: only metadata and scores may leave our infrastructure
    # (coach-chat roadmap decision 5). Flipping it needs a new product decision.
    LANGFUSE_EXPORT_CONTENT: bool = os.getenv("LANGFUSE_EXPORT_CONTENT", "false").lower() == "true"
    # HMAC salt for pseudonymous user/thread ids in traces. Required when Langfuse
    # keys are set -- observability refuses to enable without it.
    OBSERVABILITY_ID_SALT: str = os.getenv("OBSERVABILITY_ID_SALT", "")
    # USD per 1M tokens as dated windows (Gemini Developer API paid tier, standard).
    # Output price includes thinking tokens. LLM_PRICES_JSON replaces the table wholesale.
    LLM_PRICES_USD_PER_M: dict = _parse_llm_prices(os.getenv("LLM_PRICES_JSON"))

    # Coach Chat Foundation limits & deadlines
    COACH_CHAT_DAILY_NEW_TURNS_LIMIT: int = int(os.getenv("COACH_CHAT_DAILY_NEW_TURNS_LIMIT", "50"))
    COACH_CHAT_DAILY_RETRIES_LIMIT: int = int(os.getenv("COACH_CHAT_DAILY_RETRIES_LIMIT", "10"))
    COACH_CHAT_MAX_RETRIES_PER_ROOT: int = int(os.getenv("COACH_CHAT_MAX_RETRIES_PER_ROOT", "2"))
    COACH_CHAT_TURN_TIMEOUT_SECONDS: int = int(os.getenv("COACH_CHAT_TURN_TIMEOUT_SECONDS", "45"))
    COACH_CHAT_SUMMARY_TIMEOUT_SECONDS: int = int(os.getenv("COACH_CHAT_SUMMARY_TIMEOUT_SECONDS", "10"))
    COACH_CHAT_RETENTION_DAYS: int = int(os.getenv("COACH_CHAT_RETENTION_DAYS", "90"))
    COACH_CHAT_MAX_INPUT_CHARS: int = int(os.getenv("COACH_CHAT_MAX_INPUT_CHARS", "2000"))
    COACH_CHAT_DAILY_REBUILDS_LIMIT: int = int(os.getenv("COACH_CHAT_DAILY_REBUILDS_LIMIT", "5"))
    COACH_CHAT_PROMPT_LABEL: str = os.getenv(
        "COACH_CHAT_PROMPT_LABEL",
        "production" if os.getenv("ENVIRONMENT") == "production" else "staging",
    )
    COACH_CHAT_PROMPT_CACHE_TTL_SECONDS: int = int(os.getenv("COACH_CHAT_PROMPT_CACHE_TTL_SECONDS", "300"))

    NOTIFICATION_WORKER_ENABLED: bool = os.getenv("NOTIFICATION_WORKER_ENABLED", "false").lower() == "true"
    NOTIFICATION_DELIVERY_ENABLED: bool = os.getenv("NOTIFICATION_DELIVERY_ENABLED", "false").lower() == "true"
    NOTIFICATION_ALLOWLIST: str = os.getenv("NOTIFICATION_ALLOWLIST", "")
    APNS_ALLOWED_ENVIRONMENTS: str = os.getenv("APNS_ALLOWED_ENVIRONMENTS", "sandbox,production")
    APNS_KEY_ID: str = os.getenv("APNS_KEY_ID", "")
    APNS_TEAM_ID: str = os.getenv("APNS_TEAM_ID", "")
    APNS_PRIVATE_KEY_PATH: str = os.getenv("APNS_PRIVATE_KEY_PATH", "")
    APNS_TOPIC: str = os.getenv("APNS_TOPIC", "uphill.ai.app")


settings = Config()
