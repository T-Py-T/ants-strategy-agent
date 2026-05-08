"""Tests for ``scripts/benchmark.py`` — RESULT-line parsing only.

Running real games is covered by ``test_playgame_result_line.py``; this
module asserts the regex / outcome-classification logic is correct. That's
where the legacy bash benchmark broke (every game came back as a draw).
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH = REPO_ROOT / "scripts" / "benchmark.py"


@pytest.fixture(scope="module")
def benchmark_mod():
    spec = importlib.util.spec_from_file_location("benchmark_under_test", BENCH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["benchmark_under_test"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


SAMPLE_WIN = (
    "RESULT game_id=0 turns=487 winner=player_0 "
    "player_0=bot.py:rank=0,score=4,status=survived "
    "player_1=RandomBot.py:rank=1,score=1,status=eliminated"
)
SAMPLE_LOSS = (
    "RESULT game_id=0 turns=600 winner=player_1 "
    "player_0=bot.py:rank=1,score=1,status=eliminated "
    "player_1=HunterBot.py:rank=0,score=4,status=survived"
)
SAMPLE_DRAW = (
    "RESULT game_id=0 turns=1000 winner=tie(player_0,player_1) "
    "player_0=bot.py:rank=0,score=1,status=survived "
    "player_1=LeftyBot.py:rank=0,score=1,status=survived"
)
SAMPLE_4P_WIN = (
    "RESULT game_id=0 turns=850 winner=player_0 "
    "player_0=bot.py:rank=0,score=7,status=survived "
    "player_1=RandomBot.py:rank=2,score=1,status=eliminated "
    "player_2=HunterBot.py:rank=1,score=3,status=survived "
    "player_3=GreedyBot.py:rank=2,score=1,status=eliminated"
)
SAMPLE_4P_DRAW = (
    "RESULT game_id=0 turns=900 winner=tie(player_0,player_2) "
    "player_0=bot.py:rank=0,score=2,status=survived "
    "player_1=RandomBot.py:rank=1,score=1,status=eliminated "
    "player_2=HunterBot.py:rank=0,score=2,status=survived "
    "player_3=GreedyBot.py:rank=1,score=1,status=eliminated"
)


@pytest.mark.parametrize("line,expected_outcome", [
    (SAMPLE_WIN, "WIN"),
    (SAMPLE_LOSS, "LOSS"),
    (SAMPLE_DRAW, "DRAW"),
    (SAMPLE_4P_WIN, "WIN"),
    # 4-player tie that includes player_0 → DRAW (player_0 still on top)
    (SAMPLE_4P_DRAW, "DRAW"),
])
def test_outcome_classification(benchmark_mod, line, expected_outcome):
    outcome = benchmark_mod.parse_result_line(line)
    assert outcome is not None
    assert outcome.outcome_label() == expected_outcome


def test_parse_extracts_player_fields(benchmark_mod):
    o = benchmark_mod.parse_result_line(SAMPLE_WIN)
    assert o.game_id == 0
    assert o.turns == 487
    assert o.winner == "player_0"
    assert len(o.players) == 2
    assert o.players[0]["name"] == "bot.py"
    assert o.players[0]["rank"] == 0
    assert o.players[0]["score"] == 4
    assert o.players[0]["status"] == "survived"
    assert o.our_score == 4
    assert o.our_status == "survived"
    assert o.our_rank == 0


def test_parse_returns_none_when_no_result(benchmark_mod):
    assert benchmark_mod.parse_result_line("nothing useful here\n") is None
    assert benchmark_mod.parse_result_line("") is None


def test_parse_picks_last_result_line(benchmark_mod):
    """If the engine prints multiple RESULT lines (e.g. ``--rounds N``),
    we should keep the last one — that's the most recent outcome."""

    multi = "{0}\n{1}\n".format(
        SAMPLE_WIN.replace("game_id=0", "game_id=0"),
        SAMPLE_LOSS.replace("game_id=0", "game_id=1"),
    )
    o = benchmark_mod.parse_result_line(multi)
    assert o is not None
    assert o.game_id == 1
    assert o.outcome_label() == "LOSS"


def test_loss_includes_player_0_only_in_tie(benchmark_mod):
    """A tie that does *not* include player_0 should be a LOSS, not a DRAW."""

    line = (
        "RESULT game_id=0 turns=900 winner=tie(player_1,player_2) "
        "player_0=bot.py:rank=2,score=1,status=eliminated "
        "player_1=HunterBot.py:rank=0,score=3,status=survived "
        "player_2=GreedyBot.py:rank=0,score=3,status=survived"
    )
    o = benchmark_mod.parse_result_line(line)
    assert o is not None
    assert o.outcome_label() == "LOSS"


def test_matchup_summary_tally(benchmark_mod):
    s = benchmark_mod.MatchupSummary(name="vs_RandomBot")
    for line in [SAMPLE_WIN, SAMPLE_LOSS, SAMPLE_DRAW, SAMPLE_WIN]:
        s.games.append(benchmark_mod.parse_result_line(line))
    t = s.tally()
    assert t["wins"] == 2
    assert t["losses"] == 1
    assert t["draws"] == 1
    assert t["errors"] == 0
    assert t["win_rate"] == 50.0
