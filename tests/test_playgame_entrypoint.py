"""Tests for src/tools/playgame.py — the engine driver script.

Locks in the fix that allowed playgame.py to be invoked without the caller
having to set ``PYTHONPATH=.`` first; previously a bare invocation failed
with ``ModuleNotFoundError: No module named 'visualizer'`` because the
script imported relative to the repo root (which it did not put on sys.path
itself).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLAYGAME = REPO_ROOT / "src" / "tools" / "playgame.py"


def _run(*, cwd: Path, with_pythonpath: bool) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if with_pythonpath:
        env["PYTHONPATH"] = str(REPO_ROOT)
    else:
        env.pop("PYTHONPATH", None)
    return subprocess.run(
        [sys.executable, str(PLAYGAME), "--help"],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )


def test_playgame_help_runs_from_repo_root_without_pythonpath() -> None:
    """The original regression: ``python src/tools/playgame.py --help`` must
    work from the repo root with no ``PYTHONPATH`` override."""

    proc = _run(cwd=REPO_ROOT, with_pythonpath=False)
    assert proc.returncode == 0, (
        f"playgame --help failed without PYTHONPATH:\n"
        f"stdout={proc.stdout[:400]}\nstderr={proc.stderr[:400]}"
    )
    assert "playgame.py [options]" in proc.stdout


def test_playgame_help_runs_from_unrelated_cwd(tmp_path: Path) -> None:
    """Should also work from an unrelated working directory (e.g. ``/tmp``)."""

    proc = _run(cwd=tmp_path, with_pythonpath=False)
    assert proc.returncode == 0, (
        f"playgame --help failed from cwd={tmp_path}:\n"
        f"stdout={proc.stdout[:400]}\nstderr={proc.stderr[:400]}"
    )
    assert "playgame.py [options]" in proc.stdout


def test_playgame_help_still_works_with_pythonpath_set() -> None:
    """Belt-and-braces: setting ``PYTHONPATH`` (the legacy Makefile path)
    must also continue to work."""

    proc = _run(cwd=REPO_ROOT, with_pythonpath=True)
    assert proc.returncode == 0
    assert "playgame.py [options]" in proc.stdout
