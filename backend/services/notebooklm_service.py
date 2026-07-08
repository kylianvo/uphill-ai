import os
import tempfile
import time
from pathlib import Path

from notebooklm import NotebookLMClient
from notebooklm.auth import AuthTokens

from telemetry import (
    notebooklm_attempts_total,
    notebooklm_latency_seconds,
    notebooklm_tokens_received_total,
    notebooklm_tokens_sent_total,
)


class NotebookLmService:
    # Appended to every query. NotebookLM (like Gemini) will fabricate plausible-sounding
    # facts and citations when a query pushes past what its source documents cover —
    # this keeps every caller's query grounded without duplicating the instruction
    # across each service's prompt text.
    GROUNDING_SUFFIX = (
        "\n\nGrounding rule: base this answer only on your source documents. Do not invent "
        "facts, product names, or citations that are not in your documents. If your documents "
        "don't cover part of this, say so plainly instead of guessing. Answer directly in this "
        "chat as plain text — NEVER compile or save your answer as a note, guide, report, "
        "document, or file."
    )

    @classmethod
    async def query_notebook(cls, notebook_id: str, auth_json: str, query: str, service: str = "unknown") -> str:
        """
        Thread-safe method to query a NotebookLM notebook using custom auth JSON.
        Writes auth_json to a temporary file to prevent environment variable pollution
        across concurrent requests.
        """
        if not notebook_id or not auth_json:
            raise ValueError("Notebook ID and Auth JSON are required.")

        query = f"{query}{cls.GROUNDING_SUFFIX}"

        # Create a temporary file to store the credentials safely
        import uuid

        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"notebooklm_auth_{os.getpid()}_{uuid.uuid4()}.json")

        try:
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(auth_json)

            # Initialize AuthTokens from the temporary file
            auth = await AuthTokens.from_storage(path=Path(temp_file_path))

            # Query NotebookLM with latency measurement
            start_time = time.time()
            notebooklm_attempts_total.labels(service=service, status="attempt").inc()
            try:
                async with NotebookLMClient(auth) as client:
                    result = await client.chat.ask(notebook_id, query)
                    duration = time.time() - start_time

                    notebooklm_latency_seconds.labels(service=service).observe(duration)
                    notebooklm_attempts_total.labels(service=service, status="success").inc()

                    est_sent_tokens = len(query) // 4
                    est_recv_tokens = len(result.answer) // 4
                    notebooklm_tokens_sent_total.labels(service=service).inc(est_sent_tokens)
                    notebooklm_tokens_received_total.labels(service=service).inc(est_recv_tokens)

                    print(f"[NotebookLM][{service}] OK — {duration:.1f}s, ~{est_recv_tokens} tokens received")
                    return result.answer
            except Exception as e:
                notebooklm_attempts_total.labels(service=service, status="error").inc()
                print(f"[NotebookLM][{service}] ERROR: {e}")
                raise e
        except Exception as e:
            print(f"Error querying NotebookLM: {e}")
            raise e
        finally:
            # Always clean up the temp file
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass
