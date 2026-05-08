"""Shared pytest fixtures and path setup for the AntsAIBot test suite."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Ensure that both the installed `bots` / `ants` namespaces (via `src/`) and
# the analysis helpers in `scripts/` are importable when running from a fresh
# checkout, even if the project is not yet installed in editable mode.
for path in (SRC_DIR, SCRIPTS_DIR):
    spath = str(path)
    if spath not in sys.path:
        sys.path.insert(0, spath)
