from prometheus_client import Counter, Histogram

notebooklm_latency_seconds = Histogram(
    "notebooklm_latency_seconds", "Time spent waiting for NotebookLM API response (excluding cache hits)", ["service"]
)

notebooklm_tokens_sent_total = Counter(
    "notebooklm_tokens_sent_total", "Total estimated tokens sent to NotebookLM API", ["service"]
)

notebooklm_tokens_received_total = Counter(
    "notebooklm_tokens_received_total", "Total estimated tokens received from NotebookLM API", ["service"]
)

notebooklm_attempts_total = Counter(
    "notebooklm_attempts_total", "Total NotebookLM query attempts (success + error)", ["service", "status"]
)

rag_attempts_total = Counter("rag_attempts_total", "RAG generation attempts by engine", ["service", "engine", "status"])

rag_latency_seconds = Histogram("rag_latency_seconds", "RAG generation latency by engine", ["service", "engine"])

# LLM token and cost accounting (services/observability.py record_generation).
# feature is a closed set (observability.FEATURES, else "other"); never a user id.
llm_calls_total = Counter("llm_calls_total", "Gemini generation calls", ["feature", "model", "status"])

llm_tokens_total = Counter(
    "llm_tokens_total", "Gemini tokens by kind (input|output|thinking|cached)", ["feature", "model", "kind"]
)

llm_cost_usd_total = Counter("llm_cost_usd_total", "Estimated Gemini cost in USD", ["feature", "model"])

llm_latency_seconds = Histogram("llm_latency_seconds", "Gemini generation latency", ["feature", "model"])

llm_unpriced_calls_total = Counter("llm_unpriced_calls_total", "Gemini calls with no price window", ["model"])

llm_unknown_usage_calls_total = Counter(
    "llm_unknown_usage_calls_total",
    "Gemini calls whose final token usage was unavailable",
    ["feature", "status"],
)

coros_push_total = Counter("coros_push_total", "Send-to-COROS pushes by result code", ["result"])
