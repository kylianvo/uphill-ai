"""Structured JSON logging to stdout, scraped by Promtail into Loki (see
docker-compose.yml's loki/promtail services). One JSON object per line so
Loki's queries can filter on fields (service, engine, event, status) instead
of full-text grepping print() output.

Deliberately no third-party JSON-logging library: the whole formatter is
~15 lines and pulling in a dependency here risks the same kind of version
conflict that hit dbt-duckdb/protobuf earlier (see backend/requirements.txt).

Usage:
    from log_utils import get_logger
    logger = get_logger(__name__)
    logger.info("gemini prompt sent", extra={"fields": {
        "service": "plan_generator", "engine": "gemini",
        "event": "prompt_sent", "chars_sent": len(prompt),
    }})

Deliberately does NOT log full prompt/response bodies -- they can carry real
user training/health data. Log lengths, status, latency, and error text, not
payload content.
"""

import json
import logging
import sys
import time


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        fields = getattr(record, "fields", None)
        if fields:
            payload.update(fields)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
