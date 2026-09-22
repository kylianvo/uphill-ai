# Task F6 Report: Add Langfuse prompt versions with a local cold-start fallback

## Summary
Task F6 implements versioned prompt template fetching via Langfuse with in-memory caching and resilient local fallback inside `backend/services/observability.py`. It updates `METADATA_KEYS` allowlist in `backend/services/observability_policy.py`, configures prompt labels and cache TTLs in `backend/config.py`, `deploy.env.example`, and `CLAUDE.md`, and implements structured local prompt compilation with athlete profile formatting and strict Vietnamese localization rules in `backend/services/coach_prompts.py`. Comprehensive unit tests are added in `backend/tests/unit/test_coach_prompts.py`.

## Components & Contracts Implemented
1. **Langfuse Prompt Template Fetching & Caching (`observability.py`)**:
   - `PromptTemplate`: Immutable dataclass with fields `name`, `version`, `template`, `source`.
   - `_PROMPT_CACHE`: In-memory dictionary caching retrieved `PromptTemplate` objects by `(name, label)`.
   - `clear_prompt_cache()`: Utility for tests and cache busting.
   - `get_prompt_template(name, label, fallback, cache_ttl_seconds)`:
     - When Langfuse client is active, calls SDK `client.get_prompt(name, label=label, cache_ttl_seconds=cache_ttl_seconds)`.
     - On successful retrieval: caches template and returns `source="langfuse"` with stringified immutable version.
     - On network failure/outage/timeout: logs degraded warning via `_warn_once`, returns stale cached template if present, or `source="local_fallback"` with version `"local"`.
     - Athlete variables and conversation content are never transmitted to remote prompt APIs.
2. **Metadata Policy Allowlist (`observability_policy.py`)**:
   - Added `"prompt_name"`, `"prompt_version"`, `"prompt_source"` to `METADATA_KEYS` allowlist.
   - Raw prompt text and athlete variables remain strictly filtered out from traces.
3. **Configuration & Documentation**:
   - `backend/config.py`: Added `COACH_CHAT_PROMPT_LABEL` (defaulting to "production" in prod, "staging" otherwise) and `COACH_CHAT_PROMPT_CACHE_TTL_SECONDS` (defaulting to 300s).
   - `deploy.env.example` & `CLAUDE.md`: Documented configuration defaults.
4. **Local Prompt Compilation & Vietnamese Contract (`coach_prompts.py`)**:
   - Exported `PromptTemplate = observability.PromptTemplate`.
   - `get_coach_prompt_template(name, label)`: Retrieves configured template with local fallback.
   - `compile_coach_prompt(template, lang, context, evidence)`: Compiles prompt locally with structured markdown sections for Athlete Profile, Planned Workouts, Recent Activities, Retrieved Evidence, and Vietnamese runner tone/term/ban-list contract.
5. **Unit Test Verification (`tests/unit/test_coach_prompts.py`)**:
   - `test_get_prompt_template_absent_langfuse_keys`: Validates local fallback when client is None.
   - `test_get_prompt_template_success_from_langfuse`: Validates successful remote fetch, cache warming, and metadata.
   - `test_get_prompt_template_network_failure_falls_back`: Validates local fallback on network error.
   - `test_get_prompt_template_stale_cache_fallback`: Validates fallback to stale in-memory cache during remote outage.
   - `test_compile_coach_prompt_local_compilation`: Validates local formatting of athlete profile, workouts, and evidence.
   - `test_compile_coach_prompt_vietnamese_rules`: Validates strict Vietnamese register and terminology enforcement.
   - `test_get_coach_prompt_template_defaults`: Validates wrapper calling convention.
   - `test_prompt_metadata_allowlist`: Validates that trace metadata only preserves prompt name/version/source and strips raw text.

## Files Touched
- Modified: `backend/services/observability.py`
- Modified: `backend/services/observability_policy.py`
- Modified: `backend/config.py`
- Modified: `deploy.env.example`
- Modified: `CLAUDE.md`
- Modified: `backend/services/coach_prompts.py`
- Created: `backend/tests/unit/test_coach_prompts.py`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F6-brief.md`
- Created: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F6-report.md`
