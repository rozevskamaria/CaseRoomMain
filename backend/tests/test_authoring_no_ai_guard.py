from __future__ import annotations

import ast
from pathlib import Path

AUTHORING_MODULES = (
    Path(__file__).parent.parent
    / "app"
    / "services"
    / "case_authoring_service.py",
    Path(__file__).parent.parent
    / "app"
    / "repositories"
    / "case_authoring_repo.py",
)

FORBIDDEN_PREFIXES = ("app.llm", "anthropic")


def _imported_modules(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                names.add(node.module)
    return names


def test_authoring_modules_never_import_llm_client():
    for path in AUTHORING_MODULES:
        source = path.read_text()
        imports = _imported_modules(source)
        for name in imports:
            for forbidden in FORBIDDEN_PREFIXES:
                assert not name.startswith(forbidden), (
                    f"{path.name} imports {name}: clinical authoring must never "
                    "touch the LLM client"
                )
