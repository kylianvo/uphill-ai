"""`langgraph dev` entry point (see backend/langgraph.json). Refuses to load
outside a local dev database -- see dev/studio_factory.py."""

import os
import sys
from pathlib import Path

# langgraph dev loads this file by path; make backend/ importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings  # noqa: E402
from dev.studio_factory import assert_local_dev, build_studio_graph, load_studio_user_id  # noqa: E402

if "DATABASE_URL" not in os.environ:
    raise RuntimeError(
        "Set DATABASE_URL to your local dev database before running `langgraph dev` "
        "(config.py's default is not used here so the local-only guard has something to check)."
    )

assert_local_dev(settings.ENVIRONMENT, settings.DATABASE_URL)
graph = build_studio_graph(
    load_studio_user_id(os.environ),
    real_model=os.environ.get("STUDIO_REAL_MODEL") == "1",
)
