"""AST import boundary test for observability dependencies.

Ensures that langfuse, openinference, and opentelemetry are ONLY imported
in backend/services/observability.py. No other production code may import
these packages directly.
"""

import ast
from pathlib import Path

FORBIDDEN_ROOT_MODULES = {"langfuse", "openinference", "opentelemetry"}
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


def is_production_file(path: Path) -> bool:
    """Return True if path is production Python code subject to the import boundary."""
    try:
        rel = path.relative_to(BACKEND_DIR)
    except ValueError:
        return False
    parts = rel.parts

    # Exclude tests, alembic migrations, virtual environments, build artifacts, git
    if any(
        part
        in {
            "tests",
            "alembic",
            ".venv",
            "venv",
            "env",
            "__pycache__",
            ".git",
            ".pytest_cache",
            ".ruff_cache",
        }
        for part in parts
    ):
        return False

    # Exclude the wrapper itself
    if rel == Path("services/observability.py"):
        return False

    return path.suffix == ".py"


def check_ast_for_forbidden_imports(tree: ast.AST, filename: str) -> list[str]:
    """Inspect AST for imports starting with forbidden module names."""
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_ROOT_MODULES:
                    violations.append(f"{filename}:{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in FORBIDDEN_ROOT_MODULES:
                    violations.append(f"{filename}:{node.lineno}: from {node.module} import ...")
    return violations


def test_production_code_has_no_direct_observability_imports():
    """Scan all production Python files in backend/ and ensure 0 forbidden imports."""
    all_py_files = [p for p in BACKEND_DIR.rglob("*.py") if is_production_file(p)]
    assert len(all_py_files) > 10, f"Expected many production files, found {len(all_py_files)}"

    all_violations = []
    for py_file in all_py_files:
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            violations = check_ast_for_forbidden_imports(tree, str(py_file.relative_to(BACKEND_DIR)))
            all_violations.extend(violations)
        except Exception as exc:
            all_violations.append(f"{py_file}: Failed to parse AST: {exc}")

    assert not all_violations, "Found forbidden observability imports outside wrapper:\n" + "\n".join(all_violations)


def test_test_files_and_conftest_are_properly_excluded():
    """Verify that tests/conftest.py and unit tests are excluded from the boundary scan."""
    conftest = BACKEND_DIR / "tests" / "conftest.py"
    assert conftest.exists()
    assert not is_production_file(conftest)

    unit_test = BACKEND_DIR / "tests" / "unit" / "test_observability_policy.py"
    assert unit_test.exists()
    assert not is_production_file(unit_test)


def test_ast_checker_detects_injected_forbidden_imports():
    """Verify the AST checker flags forbidden Import and ImportFrom statements."""
    code = """
import langfuse
from opentelemetry import trace
import openinference.instrumentation
import math
from pydantic import BaseModel
"""
    tree = ast.parse(code)
    violations = check_ast_for_forbidden_imports(tree, "dummy.py")
    assert len(violations) == 3
    assert any("import langfuse" in v for v in violations)
    assert any("from opentelemetry" in v for v in violations)
    assert any("openinference" in v for v in violations)
