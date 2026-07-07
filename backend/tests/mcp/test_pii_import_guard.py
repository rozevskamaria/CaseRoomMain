from __future__ import annotations

import ast
import pathlib

APP_ROOT = pathlib.Path(__file__).resolve().parents[2] / "app"

ENTRYPOINT = "app.services.research_data"

BANNED_SYMBOLS = {
    "UserRepository",
    "CohortRepository",
    "_decrypt",
    "_encrypt",
    "pgp_sym_decrypt",
    "decrypt_login_name",
    "decrypt_email",
    "decrypt_full_name",
}

BANNED_MODULE_FRAGMENTS = {
    "app.repositories.user_repo",
    "app.repositories.cohort_repo",
}

ALLOWED_MODULES = {
    "app.services.research_data",
    "app.services.research_pseudonym",
    "app.repositories.research_repo",
    "app.mcp.schemas",
    "app.models.attempt",
    "app.models.event",
    "app.models.case",
    "app.models.cohort",
    "app.models.assignment",
    "app.models.user",
    "app.models.base",
    "app.models.feedback",
}


def _module_to_path(module: str) -> pathlib.Path | None:
    rel = module[len("app.") :].replace(".", "/")
    candidate = APP_ROOT / f"{rel}.py"
    if candidate.exists():
        return candidate
    pkg = APP_ROOT / rel / "__init__.py"
    if pkg.exists():
        return pkg
    return None


def _imports_of(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("app."):
                    modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("app.") and node.level == 0:
                modules.add(node.module)
    return modules


def _transitive_app_modules(entry: str) -> set[str]:
    seen: set[str] = set()
    stack = [entry]
    while stack:
        module = stack.pop()
        if module in seen:
            continue
        seen.add(module)
        path = _module_to_path(module)
        if path is None:
            continue
        for dep in _imports_of(path):
            if dep not in seen:
                stack.append(dep)
    return seen


def test_research_data_transitive_imports_no_pii_module():
    modules = _transitive_app_modules(ENTRYPOINT)
    assert "app.mcp.server" not in modules
    assert "app.mcp.mount" not in modules
    for module in modules:
        for banned in BANNED_MODULE_FRAGMENTS:
            assert module != banned, (
                f"{ENTRYPOINT} transitively imports PII module {module}"
            )


def test_research_modules_reference_no_banned_symbol():
    modules = _transitive_app_modules(ENTRYPOINT)
    research_modules = {
        m
        for m in modules
        if m.startswith("app.services.research")
        or m.startswith("app.repositories.research")
        or m.startswith("app.mcp")
    }
    research_modules.add("app.mcp.server")
    research_modules.add("app.mcp.mount")
    for module in research_modules:
        path = _module_to_path(module)
        if path is None:
            continue
        source = path.read_text()
        for banned in BANNED_SYMBOLS:
            assert banned not in source, f"{module} references banned {banned}"


def test_research_data_only_touches_allowlisted_app_modules():
    modules = _transitive_app_modules(ENTRYPOINT)
    unexpected = modules - ALLOWED_MODULES
    assert not unexpected, f"unexpected modules in research_data graph: {unexpected}"
