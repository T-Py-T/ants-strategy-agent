"""Tests for the ``RESULT`` summary line emitted by ``playgame.py``.

The benchmark suite (``scripts/benchmark.py``) parses this line to compute
WIN/LOSS/DRAW. The format is intentionally stable; if you change it, you
must update the regex in ``scripts/benchmark.py`` *and* this test.

Format:
    RESULT game_id=<int> turns=<int> winner=<str> player_0=<name>:rank=<int>,score=<int>,status=<str> ...

The "winner" field is one of:
    * ``player_<N>``    — that player has the unique top rank
    * ``tie(player_X,player_Y,...)`` — multiple top ranks
    * ``error`` / ``unknown`` — engine failure
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLAYGAME = REPO_ROOT / "src" / "tools" / "playgame.py"
SAMPLE_DIR = REPO_ROOT / "src" / "sample_bots" / "python"
MAP_2P = REPO_ROOT / "maps" / "maze" / "maze_02p_01.map"

RESULT_RE = re.compile(
    r"^RESULT\s+game_id=(?P<gid>\d+)\s+turns=(?P<turns>\d+)\s+winner=(?P<winner>\S+)\s+(?P<players>player_0=.+)$",
    re.MULTILINE,
)
PLAYER_RE = re.compile(
    r"player_(?P<idx>\d+)=(?P<name>[^:]+):rank=(?P<rank>-?\d+),score=(?P<score>-?\d+),status=(?P<status>\S+)"
)


def _play_short(tmp_path: Path, *, bot_a: str = "HoldBot.py", bot_b: str = "HoldBot.py",
                seed: int = 1, turns: int = 100) -> subprocess.CompletedProcess:
    """Run a short game between two trivial bots and capture stdout."""

    cmd = [
        sys.executable, str(PLAYGAME),
        "--player_seed", str(seed),
        "--end_wait=0.1",
        "--log_dir", str(tmp_path),
        "--turns", str(turns),
        "--map_file", str(MAP_2P),
        "{0} {1}".format(sys.executable, SAMPLE_DIR / bot_a),
        "{0} {1}".format(sys.executable, SAMPLE_DIR / bot_b),
        "--nolaunch",
    ]
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=180,
    )


def test_result_line_present_and_well_formed(tmp_path: Path) -> None:
    proc = _play_short(tmp_path)
    assert proc.returncode == 0, (
        "playgame failed:\nstdout={0}\nstderr={1}".format(proc.stdout[-500:], proc.stderr[-500:])
    )
    matches = list(RESULT_RE.finditer(proc.stdout))
    assert matches, "no RESULT line on stdout:\n{0}".format(proc.stdout[-500:])
    m = matches[-1]
    assert int(m.group("gid")) == 0
    assert int(m.group("turns")) > 0
    winner = m.group("winner")
    assert winner.startswith("player_") or winner.startswith("tie("), (
        "unexpected winner field: {0}".format(winner)
    )

    players = list(PLAYER_RE.finditer(m.group("players")))
    assert len(players) == 2, "expected 2 players, got {0}".format(len(players))
    indices = [int(p.group("idx")) for p in players]
    assert indices == [0, 1]
    for p in players:
        assert p.group("name").endswith("HoldBot.py")
        assert p.group("status") in {"survived", "eliminated", "crashed", "timeout", "invalid"}


def test_two_holdbots_tie(tmp_path: Path) -> None:
    """Two ``HoldBot``s never razing anything must tie."""

    proc = _play_short(tmp_path, bot_a="HoldBot.py", bot_b="HoldBot.py", seed=99, turns=100)
    assert proc.returncode == 0
    m = list(RESULT_RE.finditer(proc.stdout))[-1]
    winner = m.group("winner")
    assert winner.startswith("tie("), (
        "two HoldBots should tie, got winner={0}".format(winner)
    )
    assert "player_0" in winner and "player_1" in winner


def test_json_mode_suppresses_result_line(tmp_path: Path) -> None:
    """``--json`` mode should still print useful machine-readable output but
    the ``RESULT`` summary line is suppressed (callers picked one or the other)."""

    cmd = [
        sys.executable, str(PLAYGAME),
        "--player_seed", "1",
        "--end_wait=0.1",
        "--log_dir", str(tmp_path),
        "--turns", "100",
        "--map_file", str(MAP_2P),
        "--json",
        "{0} {1}".format(sys.executable, SAMPLE_DIR / "HoldBot.py"),
        "{0} {1}".format(sys.executable, SAMPLE_DIR / "HoldBot.py"),
        "--nolaunch",
    ]
    proc = subprocess.run(
        cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0
    assert not RESULT_RE.search(proc.stdout), (
        "RESULT line should be suppressed in --json mode"
    )
    assert '"score"' in proc.stdout, "JSON output should include scores"
