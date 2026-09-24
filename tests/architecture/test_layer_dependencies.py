import ast
from pathlib import Path

import pytest

SOURCE_ROOT = Path("src/reliable_webhook_api")
FORBIDDEN_IMPORTS = ("fastapi", "sqlalchemy", "reliable_webhook_api.infrastructure")


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)

    return modules


@pytest.mark.parametrize("layer", ["domain", "application"])
def test_core_layers_do_not_import_framework_or_infrastructure(layer: str) -> None:
    violations: list[str] = []

    for path in (SOURCE_ROOT / layer).rglob("*.py"):
        for module in imported_modules(path):
            if module.startswith(FORBIDDEN_IMPORTS):
                violations.append(f"{path}: {module}")

    assert violations == []
