"""Consistency tests between the README and the actual project.

Catches README rot: every Make target the README points users at must
actually exist, every directory mentioned in the Project Structure tree
must actually exist, and the install-extras table must match
``pyproject.toml``'s ``[project.optional-dependencies]``.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"
MAKEFILE = REPO_ROOT / "Makefile"


def _readme() -> str:
    return README.read_text()


def _make_targets() -> set[str]:
    """Parse the Makefile and return the set of declared target names."""

    text = MAKEFILE.read_text()
    targets: set[str] = set()
    for line in text.splitlines():
        match = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*)\s*:", line)
        if match:
            targets.add(match.group(1))
    return targets


def _make_targets_referenced_in_readme() -> set[str]:
    """Find tokens of the form ``make <target>`` inside fenced code blocks.

    Restricting the search to code blocks avoids matching prose like
    "make strategic decisions" or "we make better choices".
    """

    text = _readme()
    code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", text, flags=re.DOTALL)
    targets: set[str] = set()
    for block in code_blocks:
        for line in block.splitlines():
            # strip inline comments to ignore stuff after ``#``
            stripped = line.split("#", 1)[0].strip()
            for match in re.finditer(r"\bmake\s+([a-zA-Z][\w-]*)", stripped):
                targets.add(match.group(1))
    return targets


def test_every_make_target_in_readme_exists() -> None:
    referenced = _make_targets_referenced_in_readme()
    declared = _make_targets()
    missing = referenced - declared
    assert not missing, (
        f"README references make targets that don't exist in Makefile: "
        f"{sorted(missing)}"
    )


def test_readme_pyproject_extras_table_is_accurate() -> None:
    """The 'Three optional dependency extras' table in the README must match
    pyproject.toml's ``[project.optional-dependencies]`` section."""

    with PYPROJECT.open("rb") as fp:
        meta = tomllib.load(fp)
    declared = set(meta["project"]["optional-dependencies"].keys())

    text = _readme()
    # Look for "[test]", "[analysis]", "[dev]" mentioned in the table.
    documented = {
        name for name in ("test", "analysis", "dev")
        if f"`[{name}]`" in text
    }

    assert documented == declared, (
        f"README documents extras {sorted(documented)} but pyproject "
        f"defines {sorted(declared)} — keep them in sync."
    )


def test_project_structure_tree_lists_real_directories() -> None:
    """Each directory mentioned with a trailing ``/`` in the Project Structure
    tree should actually exist in the repo."""

    text = _readme()
    # Extract the fenced code block under 'Project Structure'.
    match = re.search(
        r"## Project Structure\s*\n+```\n(?P<body>.*?)```",
        text,
        re.DOTALL,
    )
    assert match, "could not locate the Project Structure code block"
    body = match.group("body")

    # Pull out lines that look like ``├── name/`` or ``│   ├── name/``
    dir_pattern = re.compile(r"[├└]──\s+([A-Za-z_.][\w./-]*?/)")
    referenced_dirs = {
        m.group(1).rstrip("/")
        for line in body.splitlines()
        for m in [dir_pattern.search(line)]
        if m
    }

    missing: list[str] = []
    for rel in referenced_dirs:
        # The tree shows nested entries with only their leaf name; rather
        # than reconstructing the full hierarchy from the indentation,
        # accept the directory if any directory of that name exists
        # anywhere under the repo (typical case for `mapgen/`, `ants/`, etc.).
        rel_parts = rel.split("/")
        target = rel_parts[-1]
        # Look for any directory ending in this name under repo root.
        found = any(
            p.is_dir() and p.name == target
            for p in REPO_ROOT.rglob(target)
            # ignore noise from .venv / build artifacts
            if ".venv" not in p.parts and "__pycache__" not in p.parts
        )
        if not found:
            missing.append(rel)

    assert not missing, (
        f"README Project Structure references non-existent directories: {missing}"
    )


def test_make_help_lists_pytest_target() -> None:
    """``make help`` should advertise the pytest target so contributors find it."""

    proc = subprocess.run(
        ["make", "help"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0
    assert "pytest" in proc.stdout, (
        "`make help` output should mention the pytest target.\n"
        f"Got:\n{proc.stdout}"
    )
