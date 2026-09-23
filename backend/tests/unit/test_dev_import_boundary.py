"""AST import boundary test for the dev-only Studio tooling.

Ensures that no production module imports `dev` (backend/dev/), which only
exists for local LangGraph Studio debugging and asserts a local-only
database guard that production code must never rely on or bypass.
"""

import ast
from pathlib import Path

FORBIDDEN_ROOT_MODULES = {"dev"}
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


def is_production_file(path: Path) -> bool:
    """Return True if path is production Python code subject to the import boundary."""
    try:
        rel = path.relative_to(BACKEND_DIR)
    except ValueError:
        return False
    parts = rel.parts

    # Exclude dev/ itself, tests, scripts, virtual environments, build artifacts, git
    if any(
        part
        in {
            "dev",
            "tests",
            "scripts",
            "alembic",
            ".venv",
            ".venv-studio",
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
            if node.module and node.level == 0:
                root = node.module.split(".")[0]
                if root in FORBIDDEN_ROOT_MODULES:
                    violations.append(f"{filename}:{node.lineno}: from {node.module} import ...")
    return violations


def test_production_code_has_no_dev_imports():
    """Scan all production Python files in backend/ and ensure 0 imports of `dev`."""
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

    assert not all_violations, "Found forbidden `dev` imports outside backend/dev/:\n" + "\n".join(all_violations)


def test_ast_checker_detects_injected_dev_import():
    """Verify the AST checker flags Import and ImportFrom statements referencing `dev`."""
    code = """
import dev
from dev import studio_factory
import math
from pydantic import BaseModel
"""
    tree = ast.parse(code)
    violations = check_ast_for_forbidden_imports(tree, "dummy.py")
    assert len(violations) == 2
    assert any("import dev" in v for v in violations)
    assert any("from dev import" in v for v in violations)
