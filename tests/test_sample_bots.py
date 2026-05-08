"""Smoke tests that drive each Python sample bot through one full turn.

Catches Python 2 -> 3 regressions (e.g. ``shuffle(dict.keys())``) that only
manifest during ``do_turn`` rather than at import time. Each bot is spawned
as a subprocess in the same way the engine's playgame.py would, fed a
canned setup + one ``go`` turn, and inspected for clean stderr output.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_BOTS_DIR = REPO_ROOT / "src" / "sample_bots" / "python"

# Bots intended to behave correctly. Other bots in this directory exist
# *deliberately* to exercise the engine's misbehavior handling
# (ErrorBot, InvalidBot, TimeoutBot) and are excluded here.
WELL_BEHAVED_BOTS = ["RandomBot", "HunterBot", "GreedyBot", "LeftyBot", "HoldBot"]

SETUP_BLOCK = (
    "turn 0\n"
    "rows 6\n"
    "cols 6\n"
    "turns 5\n"
    "turntime 1000\n"
    "loadtime 3000\n"
    "viewradius2 5\n"
    "attackradius2 5\n"
    "spawnradius2 1\n"
    "player_seed 1\n"
    "ready\n"
)
TURN_BLOCK = "turn 1\na 1 1 0\ngo\n"


def _run_bot(bot_name: str, *, with_turn: bool) -> tuple[str, str]:
    """Spawn ``bot_name``, feed it ``SETUP_BLOCK`` (plus optionally one turn),
    capture stdout/stderr, then terminate.

    The sample bots' ``Ants.run()`` event loop never exits on stdin EOF
    (``readline()`` returns ``''`` instead of raising), so we use a short
    timeout and kill the process — what we care about is whatever the bot
    wrote before being killed.
    """

    bot_path = SAMPLE_BOTS_DIR / f"{bot_name}.py"
    proc = subprocess.Popen(
        [sys.executable, str(bot_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdin_payload = SETUP_BLOCK + (TURN_BLOCK if with_turn else "")
    try:
        out, err = proc.communicate(input=stdin_payload, timeout=1.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
    return out, err


@pytest.mark.parametrize("bot_name", WELL_BEHAVED_BOTS)
def test_sample_bot_setup_phase_is_clean(bot_name: str) -> None:
    """Each well-behaved bot must accept the ``ready`` setup block silently."""

    out, err = _run_bot(bot_name, with_turn=False)
    assert "go" in out, f"{bot_name} did not respond to setup with 'go'"
    assert err.strip() == "", (
        f"{bot_name} wrote unexpected stderr during setup:\n{err}"
    )


@pytest.mark.parametrize("bot_name", WELL_BEHAVED_BOTS)
def test_sample_bot_one_turn_no_traceback(bot_name: str) -> None:
    """Each well-behaved bot must run a single ``go`` turn without raising.

    This is the regression backstop for the ``shuffle(AIM.keys())`` Python 3
    breakage in RandomBot — and any similar Py2-only patterns introduced in
    other sample bots in the future.
    """

    out, err = _run_bot(bot_name, with_turn=True)
    assert "Traceback" not in err, (
        f"{bot_name} raised a Python exception during do_turn:\n{err}"
    )
    assert "TypeError" not in err and "AttributeError" not in err, (
        f"{bot_name} produced an error during do_turn:\n{err}"
    )
