"""Compile + import smoke tests for src/tools/mapgen/.

These scripts originated as Python 2 code and several files used Python-2
``print`` statements that fail to parse under Python 3. The tests here lock
in the Python 3 port.
"""

from __future__ import annotations

import importlib.util
import py_compile
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAPGEN_DIR = REPO_ROOT / "src" / "tools" / "mapgen"


def _all_py_files() -> list[Path]:
    return sorted(p for p in MAPGEN_DIR.glob("*.py"))


@pytest.mark.parametrize("path", _all_py_files(), ids=lambda p: p.name)
def test_mapgen_script_compiles(path: Path) -> None:
    """Every script under src/tools/mapgen/ must parse cleanly under Python 3."""

    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        pytest.fail(f"{path.name} failed to compile under Python 3:\n{exc}")


@pytest.mark.parametrize(
    "module_name",
    ["map", "asymmetric_mapgen", "symmetric_mapgen"],
)
def test_mapgen_module_imports(module_name: str) -> None:
    """The non-CLI mapgen modules must be importable under Python 3.

    These modules historically used ``from sys import maxint`` (Python 2
    only); the port should either use a try/except fallback or
    ``sys.maxsize`` directly.
    """

    sys_path_prepended = str(MAPGEN_DIR)
    if sys_path_prepended not in sys.path:
        sys.path.insert(0, sys_path_prepended)
    try:
        spec = importlib.util.find_spec(module_name)
        assert spec is not None, f"could not locate {module_name!r}"
        importlib.import_module(module_name)
    finally:
        sys.path.remove(sys_path_prepended)


def test_mapgen_print_map_runs_as_script() -> None:
    """``asymmetric_mapgen.py`` should produce a valid map header when run as a script.

    This is a stronger backstop than ``py_compile``: it actually executes
    the ``__main__`` block, which in this script generates and prints a map.
    """

    proc = subprocess.run(
        [sys.executable, str(MAPGEN_DIR / "asymmetric_mapgen.py")],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, (
        f"asymmetric_mapgen.py exited {proc.returncode}\n"
        f"stdout: {proc.stdout[:500]}\n"
        f"stderr: {proc.stderr[:500]}"
    )
    # First three lines should be ``rows N``, ``cols N``, ``players N``
    head = [line for line in proc.stdout.splitlines() if line][:3]
    assert head[0].startswith("rows ")
    assert head[1].startswith("cols ")
    assert head[2].startswith("players ")
