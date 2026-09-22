# Task F6 Brief: Add Langfuse prompt versions with a local cold-start fallback

## Objective
Implement Langfuse prompt template versioning with in-memory caching and local fallback in `backend/services/observability.py`. Update metadata allowlist in `backend/services/observability_policy.py`. Add configuration in `backend/config.py`, `deploy.env.example`, and `CLAUDE.md`. Implement local compilation and Vietnamese contract integration in `backend/services/coach_prompts.py`. Verify with unit tests in `backend/tests/unit/test_coach_prompts.py`.

## File Targets
- Modify: `backend/services/observability.py`
- Modify: `backend/services/observability_policy.py`
- Modify: `backend/config.py`
- Modify: `deploy.env.example`
- Modify: `CLAUDE.md`
- Modify: `backend/services/coach_prompts.py`
- Test: `backend/tests/unit/test_coach_prompts.py`
- Report: `.superpowers/sdd/2026-09-20-coach-chat-foundation/task-F6-report.md`

## Specifications
1. **Langfuse Prompt Versioning & Cache (`observability.py`)**:
   - `PromptTemplate` dataclass: `name`, `version`, `template`, `source`.
   - `_PROMPT_CACHE`: in-memory dict keyed by `(name, label)`.
   - `clear_prompt_cache()`: clears the cache.
   - `get_prompt_template(name, label, fallback, cache_ttl_seconds)`:
     - If Langfuse client is initialized, calls `client.get_prompt(name, label=label, cache_ttl_seconds=cache_ttl_seconds)`.
     - On success: saves to `_PROMPT_CACHE` and returns `PromptTemplate(name=name, version=str(version), template=str(prompt), source="langfuse")`.
     - On failure/outage/timeout: logs warning via `_warn_once`, returns stale cached template if present, or `PromptTemplate(name=name, version="local", template=fallback, source="local_fallback")`.
     - Athlete variables and messages are never passed to remote prompt API.
2. **Metadata Allowlist (`observability_policy.py`)**:
   - Allowlist trace metadata keys: `"prompt_name"`, `"prompt_version"`, `"prompt_source"`.
3. **Configuration (`config.py`, `deploy.env.example`, `CLAUDE.md`)**:
   - `COACH_CHAT_PROMPT_LABEL`: defaults to "production" in prod, "staging" otherwise.
   - `COACH_CHAT_PROMPT_CACHE_TTL_SECONDS`: defaults to 300 seconds.
4. **Local Prompt Compilation (`coach_prompts.py`)**:
   - Re-exports `PromptTemplate = observability.PromptTemplate`.
   - `get_coach_prompt_template(name, label)`: retrieves prompt template via observability.
   - `compile_coach_prompt(template, lang, context, evidence)`: compiles prompt text, athlete profile, plan workouts, evidence excerpts, and Vietnamese localization rules locally.
