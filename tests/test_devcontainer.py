"""Structural sanity tests for `.devcontainer/devcontainer.json`.

Locks in the migration off of deprecated VSCode Python-extension settings
(`python.linting.*`, `python.formatting.provider`) onto the modern
per-extension equivalents (`pylint.enabled`, `[python].editor.defaultFormatter`).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DEVCONTAINER = REPO_ROOT / ".devcontainer" / "devcontainer.json"


def _load_devcontainer() -> dict:
    """Parse devcontainer.json, tolerating // comments (JSONC)."""

    raw = DEVCONTAINER.read_text()
    # Strip ``// line`` style comments — devcontainer.json is JSONC.
    stripped = re.sub(r"^\s*//.*$", "", raw, flags=re.MULTILINE)
    return json.loads(stripped)


@pytest.fixture(scope="module")
def devcontainer() -> dict:
    return _load_devcontainer()


def test_devcontainer_parses(devcontainer: dict) -> None:
    assert devcontainer["name"] == "AntsAIBot Development"
    assert devcontainer["workspaceFolder"] == "/app"


def test_no_deprecated_python_extension_keys(devcontainer: dict) -> None:
    """Should not reference settings deprecated in `ms-python.python` >= 2024.x."""

    settings = devcontainer["customizations"]["vscode"]["settings"]
    deprecated = {
        "python.linting.enabled",
        "python.linting.pylintEnabled",
        "python.formatting.provider",
    }
    leftover = deprecated & set(settings.keys())
    assert not leftover, f"deprecated VSCode settings still present: {leftover}"


def test_modern_lint_and_format_settings_present(devcontainer: dict) -> None:
    settings = devcontainer["customizations"]["vscode"]["settings"]
    assert settings.get("pylint.enabled") is True, (
        "modern `pylint.enabled` (from ms-python.pylint) should be true"
    )
    python_lang = settings.get("[python]")
    assert isinstance(python_lang, dict), "missing `[python]` language block"
    assert python_lang.get("editor.defaultFormatter") == "ms-python.black-formatter"


def test_post_create_command_uses_uv(devcontainer: dict) -> None:
    """The bootstrap should hydrate the project via uv (matches the
    project's canonical install workflow), not via raw pip."""

    assert "uv sync" in devcontainer["postCreateCommand"]
    assert "--all-extras" in devcontainer["postCreateCommand"]


def test_python_interpreter_points_to_uv_venv(devcontainer: dict) -> None:
    settings = devcontainer["customizations"]["vscode"]["settings"]
    assert (
        settings["python.defaultInterpreterPath"]
        == "/app/.venv/bin/python"
    ), "interpreter path should resolve to the uv-managed venv"


def test_pytest_test_runner_configured(devcontainer: dict) -> None:
    settings = devcontainer["customizations"]["vscode"]["settings"]
    assert settings.get("python.testing.pytestEnabled") is True
    assert settings.get("python.testing.pytestArgs") == ["tests/"]
