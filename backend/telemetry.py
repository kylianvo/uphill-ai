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
