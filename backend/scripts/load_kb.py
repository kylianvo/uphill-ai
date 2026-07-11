"""Load committed kb_seed/*.json files into the current environment's DB + Qdrant.

Usage (from backend/):  python scripts/load_kb.py [--domain gear|nutrition|scheduler|all]
Equivalent to POST /api/kb/import, for shells/CI where an admin session is awkward.
"""

import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings  # noqa: E402
from services.kb_distiller import DOMAINS, HAND_CURATED_DOMAINS, load_seed  # noqa: E402

IMPORTABLE_DOMAINS = DOMAINS + HAND_CURATED_DOMAINS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="all", choices=[*IMPORTABLE_DOMAINS, "all"])
    args = parser.parse_args()
    domains = list(IMPORTABLE_DOMAINS) if args.domain == "all" else [args.domain]
    for domain in domains:
        try:
            count = load_seed(domain, settings.GEMINI_API_KEY or None)
            print(f"{domain}: loaded {count} chunks")
        except (FileNotFoundError, RuntimeError) as e:
            print(f"{domain}: SKIPPED — {e}")


if __name__ == "__main__":
    main()
