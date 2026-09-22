# LLM Observability & LLMOps Release Report

## Executive Summary

Sub-project 1 of the Coach Chat roadmap (LLM Observability and Standalone Feature LLMOps) is complete and verified across all scheduled phases:
- **Task H1**: Metadata-only boundary, attribute sanitizer, media upload block, bounded latch/cleanup.
- **Task H2**: Canonical single-owner generation accounting, native Langfuse cost/token mapping, unknown-usage metrics, bounded Prometheus cardinality, pricing window validation.
- **Task 11**: Direct Plan Generator instrumentation (primary Gemini, reduced-prompt retry, rule-based non-billable fallback, single-workout, week-narrative, and scheduler embeddings).
- **Task 12**: Standalone catalog and knowledge flows (Gear Finder, Nutrition Lab, KB Distiller, Knowledge Extractor bilingual card translations and podcast web discovery).
- **Task 13**: Synthetic evaluation experiments publication (`push_experiment`, `golden_eval.py --push-langfuse`) without duplicate paid inference, and production AST import boundary enforcement.
- **Task H3**: Grafana dashboard provisioning, operator documentation, privacy verification, and staged release gates.

---

## Operator Guide & Configuration

### Environment Variables

All variables live in `backend/.env` (reference: `deploy.env.example`):

| Variable | Description | Default / Production Value |
| :--- | :--- | :--- |
| `LANGFUSE_PUBLIC_KEY` | Langfuse project public key | Empty (disabled) |
| `LANGFUSE_SECRET_KEY` | Langfuse project secret key | Empty (disabled) |
| `LANGFUSE_BASE_URL` | Langfuse API host (EU data residency) | `https://cloud.langfuse.com` |
| `LANGFUSE_ENVIRONMENT` | Tag for traces and generations | `production` / `staging` / `development` |
| `LANGFUSE_SAMPLE_RATE` | Trace sampling ratio (0.0 to 1.0) | `1.0` |
| `LANGFUSE_TIMEOUT` | Background exporter timeout in seconds | `5` |
| `LANGFUSE_EXPORT_CONTENT` | Content export gate (**MUST BE FALSE**) | `false` |
| `OBSERVABILITY_ID_SALT` | Secret HMAC salt for user/thread pseudonyms | Required when keys are set |
| `LLM_PRICES_JSON` | Optional JSON string overriding model rates | None (uses official price table) |

### No-Key / Disabled Mode
When `LANGFUSE_PUBLIC_KEY` or `LANGFUSE_SECRET_KEY` is not configured:
- Traces and generations are completely bypassed (no-op).
- No background workers or network connections are opened.
- Exporter failures or misconfigurations never delay or abort application requests.
- Prometheus counters (`llm_calls_total`, `llm_tokens_total`, `llm_cost_usd_total`, `llm_latency_seconds`, `llm_unknown_usage_calls_total`) continue to record accurately from in-memory metadata.

### How to Disable Immediately
To disable Langfuse in any environment, comment out or empty `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` in `backend/.env` and restart the backend container.

---

## Data Privacy & Export Boundary

### Exported vs Omitted Data

| Category | Exported to Langfuse | Retained / Filtered Out |
| :--- | :--- | :--- |
| **Prompts & Messages** | ❌ None | Blocked by `LANGFUSE_EXPORT_CONTENT=false` and final sanitizer |
| **Model Completions** | ❌ None | Blocked by `LANGFUSE_EXPORT_CONTENT=false` and final sanitizer |
| **Athlete Identity** | Pseudonym only (`hmac-sha256(user_id, salt)`) | Raw user IDs, emails, names never leave server |
| **Health / Injury Notes** | ❌ None | Blocked from metadata, traces, and metrics |
| **Retrieval Data** | Numeric scores & 12-char SHA1 refs only | Chunk content, titles, athlete queries omitted |
| **Catalog Metadata** | Integer counts (`catalog_entries`, `cache_hit`) | Full catalog payload omitted from traces |
| **Token Usage & Costs** | Input/Output/Thinking/Cached tokens & USD | Autorated via official Gemini rates |
| **Prometheus Labels** | Bounded closed sets (`feature`, `model`, `status`) | No athlete identifiers or arbitrary strings |

---

## Synthetic Experiments & Evaluation

- `backend/scripts/golden_eval.py` supports `--push-langfuse` for offline evaluation without paid re-inference.
- Only committed synthetic fixtures (`gear`, `nutrition`, `scheduler`) are eligible (`synthetic=True` required). Private database rows or athlete logs are strictly denied by `push_experiment`.
- Metrics published: `latency_s`, `engine_is_gemini`, `workout_count`, and `catalog_membership_valid` (which replaces misleading hallucination guard metrics).

---

## Grafana Dashboard Provisioning

The main dashboard (`grafana/dashboards/uphill_dashboard.json`) has been enriched with four dedicated Prometheus panels:
1. **LLM Estimated Cost (USD) by Feature**: tracks rate of spend across `plan_generator`, `gear_finder`, `nutrition_lab`, `kb_distill`, `knowledge_cards`.
2. **LLM Calls by Feature & Status**: real-time RPS and error rates by feature.
3. **LLM P95 Latency by Feature**: 95th percentile latency from `llm_latency_seconds`.
4. **LLM Unknown Usage & Unpriced Calls**: observability integrity monitoring to ensure no silent unmetered calls occur.

---

## Foundation Release Gates

1. **Prompt Management**: Deferred as planned for the future Coach Chat foundation (LangGraph chat agent, Sub-project 2). Not shipped in direct feature generation.
2. **ChatGoogleGenerativeAI Nested Canary**: Testing nested OpenInference + Google GenAI auto-instrumentation is recorded as a mandatory preflight gate before shipping Sub-project 2 (LangGraph chat agent).
3. **AST Boundary Invariant**: Verified in `tests/unit/test_observability_boundary.py` — no module outside `backend/services/observability.py` may import `langfuse`, `openinference`, or `opentelemetry`.
