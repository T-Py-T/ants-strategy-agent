"""Tests for ``src/bots/xathis_bot.py`` — the Python port of xathis.

Locks in the foundations (Tile / Ant data classes, torus geometry,
combat distance predicates) so that subsequent commits porting individual
phases (food, fight, etc.) don't regress them.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_BOTS = REPO_ROOT / "src" / "bots"


@pytest.fixture(scope="module")
def xb():
    """Import ``src.bots.xathis_bot`` while making sure ``src/bots/ants.py``
    (the bot-side helper) is what ``from ants import *`` resolves to."""

    # Save and replace ``ants`` in sys.modules so xathis_bot's ``from ants
    # import ...`` gets the bot helper, not the engine package.
    prev_ants = sys.modules.get("ants")
    spec_helper = importlib.util.spec_from_file_location(
        "ants", SRC_BOTS / "ants.py"
    )
    assert spec_helper and spec_helper.loader
    helper = importlib.util.module_from_spec(spec_helper)
    sys.modules["ants"] = helper
    spec_helper.loader.exec_module(helper)  # type: ignore[union-attr]

    spec = importlib.util.spec_from_file_location(
        "xathis_bot_under_test", SRC_BOTS / "xathis_bot.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["xathis_bot_under_test"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    yield mod

    # restore
    if prev_ants is None:
        sys.modules.pop("ants", None)
    else:
        sys.modules["ants"] = prev_ants


def _make_bot(xb, rows: int = 20, cols: int = 30):
    bot = xb.XathisBot()
    bot.rows = rows
    bot.cols = cols
    bot.tiles = [[xb.Tile(r, c) for c in range(cols)] for r in range(rows)]
    for r in range(rows):
        for c in range(cols):
            t = bot.tiles[r][c]
            t.neighbors = (
                bot.tiles[(r - 1) % rows][c],
                bot.tiles[r][(c + 1) % cols],
                bot.tiles[(r + 1) % rows][c],
                bot.tiles[r][(c - 1) % cols],
            )
    return bot


# ---------------------------------------------------------------------------
# Torus geometry
# ---------------------------------------------------------------------------
class TestTorusDistance:
    """Verify that ``dist`` / ``dist_row`` / ``dist_col`` wrap correctly."""

    def test_zero_distance(self, xb):
        bot = _make_bot(xb, 20, 30)
        t = bot.tiles[5][5]
        assert bot.dist(t, t) == 0
        assert bot.dist_row(t, t) == 0
        assert bot.dist_col(t, t) == 0

    def test_simple_distance_no_wrap(self, xb):
        bot = _make_bot(xb, 20, 30)
        a = bot.tiles[5][5]
        b = bot.tiles[7][9]
        assert bot.dist_row(a, b) == 2
        assert bot.dist_col(a, b) == 4
        assert bot.dist(a, b) == 6

    def test_row_wrap_picks_short_side(self, xb):
        bot = _make_bot(xb, 20, 30)
        a = bot.tiles[1][10]
        b = bot.tiles[19][10]
        # direct = 18, wrap = 2 → 2
        assert bot.dist_row(a, b) == 2
        assert bot.dist(a, b) == 2

    def test_col_wrap_picks_short_side(self, xb):
        bot = _make_bot(xb, 20, 30)
        a = bot.tiles[5][2]
        b = bot.tiles[5][28]
        # direct = 26, wrap = 4 → 4
        assert bot.dist_col(a, b) == 4
        assert bot.dist(a, b) == 4

    def test_distance_is_symmetric(self, xb):
        bot = _make_bot(xb, 20, 30)
        a = bot.tiles[3][7]
        b = bot.tiles[15][22]
        assert bot.dist(a, b) == bot.dist(b, a)
        assert bot.dist_row(a, b) == bot.dist_row(b, a)
        assert bot.dist_col(a, b) == bot.dist_col(b, a)


# ---------------------------------------------------------------------------
# Combat distance predicates (alpha < beta < gamma)
# ---------------------------------------------------------------------------
# Reference: ``Strategy.java:1726, 1732, 1742`` — we mirror these exactly.
#
# The Ants AI Challenge attack rule (attackradius2 = 5) means an ant kills
# any enemy within Euclidean^2 ≤ 5: i.e. (dr,dc) ∈ {(0,0),(0,1),(1,0),(1,1),
# (0,2),(2,0),(1,2),(2,1)}. xathis uses Manhattan-on-torus rather than
# Euclidean^2, but his alpha/beta/gamma predicates exactly cover the
# cases his combat search needs.
class TestCombatDistances:
    def test_alpha_dist_self(self, xb):
        bot = _make_bot(xb, 30, 30)
        t = bot.tiles[10][10]
        assert bot.is_alpha_dist(t, t) is True

    def test_alpha_dist_kills_at_attack_range(self, xb):
        bot = _make_bot(xb, 30, 30)
        a = bot.tiles[10][10]
        # All Euclidean^2 ≤ 5 cells should be alpha (xathis includes a
        # superset).
        for dr, dc in [(0, 1), (1, 0), (1, 1), (0, 2), (2, 0), (1, 2), (2, 1)]:
            b = bot.tiles[10 + dr][10 + dc]
            assert bot.is_alpha_dist(a, b), f"expected alpha for d=({dr},{dc})"

    def test_alpha_dist_not_at_distance_3(self, xb):
        bot = _make_bot(xb, 30, 30)
        a = bot.tiles[10][10]
        # A cell with dr+dc = 4 (e.g. (2,2)) — not in alpha
        b = bot.tiles[12][12]
        assert bot.is_alpha_dist(a, b) is False
        # (3,0) — out of range
        b2 = bot.tiles[13][10]
        assert bot.is_alpha_dist(a, b2) is False

    def test_beta_strictly_includes_alpha(self, xb):
        bot = _make_bot(xb, 30, 30)
        a = bot.tiles[10][10]
        for dr in range(0, 5):
            for dc in range(0, 5):
                b = bot.tiles[10 + dr][10 + dc]
                if bot.is_alpha_dist(a, b):
                    assert bot.is_beta_dist(a, b), (
                        f"alpha implies beta failed for d=({dr},{dc})"
                    )

    def test_beta_excludes_4_0_and_0_4(self, xb):
        """xathis explicitly excludes the (4,0) and (0,4) corners from
        beta (Strategy.java:1736)."""

        bot = _make_bot(xb, 30, 30)
        a = bot.tiles[10][10]
        assert bot.is_beta_dist(a, bot.tiles[14][10]) is False  # (4,0)
        assert bot.is_beta_dist(a, bot.tiles[10][14]) is False  # (0,4)
        # but (3,1) IS in beta
        assert bot.is_beta_dist(a, bot.tiles[13][11]) is True

    def test_gamma_strictly_includes_beta(self, xb):
        bot = _make_bot(xb, 30, 30)
        a = bot.tiles[10][10]
        for dr in range(0, 6):
            for dc in range(0, 6):
                b = bot.tiles[10 + dr][10 + dc]
                if bot.is_beta_dist(a, b):
                    assert bot.is_gamma_dist(a, b), (
                        f"beta implies gamma failed for d=({dr},{dc})"
                    )

    def test_gamma_excludes_5_0(self, xb):
        bot = _make_bot(xb, 30, 30)
        a = bot.tiles[10][10]
        assert bot.is_gamma_dist(a, bot.tiles[15][10]) is False  # (5,0)
        assert bot.is_gamma_dist(a, bot.tiles[10][15]) is False  # (0,5)
        assert bot.is_gamma_dist(a, bot.tiles[14][11]) is True   # (4,1)

    def test_combat_distances_wrap_on_torus(self, xb):
        bot = _make_bot(xb, 20, 30)
        a = bot.tiles[1][1]
        # b at (19, 29) = (-2, -2) on torus → alpha
        b = bot.tiles[19][29]
        assert bot.dist_row(a, b) == 2
        assert bot.dist_col(a, b) == 2
        assert bot.is_alpha_dist(a, b) is False  # (2,2) → out
        # but (19, 0) = (-2, -1) = (2, 1) → alpha
        c = bot.tiles[19][0]
        assert bot.is_alpha_dist(a, c) is True


# ---------------------------------------------------------------------------
# Tile graph wiring
# ---------------------------------------------------------------------------
class TestTileGraph:
    def test_neighbors_are_torus_wrapped(self, xb):
        bot = _make_bot(xb, 5, 5)
        t = bot.tiles[0][0]
        names = {n.row * 5 + n.col for n in t.neighbors}
        assert names == {
            0 * 5 + 1,   # east
            0 * 5 + 4,   # west wrap
            1 * 5 + 0,   # south
            4 * 5 + 0,   # north wrap
        }

    def test_dir_to_cardinal(self, xb):
        bot = _make_bot(xb, 10, 10)
        t = bot.tiles[5][5]
        assert t.dir_to(bot.tiles[4][5]) == "n"
        assert t.dir_to(bot.tiles[6][5]) == "s"
        assert t.dir_to(bot.tiles[5][6]) == "e"
        assert t.dir_to(bot.tiles[5][4]) == "w"

    def test_dir_to_wrap(self, xb):
        bot = _make_bot(xb, 10, 10)
        # tile (0,0) → tile (9,0) : that's "north" (wraps)
        assert bot.tiles[0][0].dir_to(bot.tiles[9][0]) == "n"
        # tile (9,9) → tile (0,9) : that's "south" (wraps)
        assert bot.tiles[9][9].dir_to(bot.tiles[0][9]) == "s"
        # tile (5,0) → tile (5,9) : "west" (wraps)
        assert bot.tiles[5][0].dir_to(bot.tiles[5][9]) == "w"


# ---------------------------------------------------------------------------
# Ant / Mission data classes
# ---------------------------------------------------------------------------
class TestAntAndMission:
    def test_ant_defaults(self, xb):
        bot = _make_bot(xb, 5, 5)
        a = xb.Ant(bot.tiles[2][2])
        assert a.tile is bot.tiles[2][2]
        assert a.has_moved is False
        assert a.is_dangered is False
        assert a.is_grouped is False
        assert a.gamma_dist_enemies == []
        assert a.closest_enemy_dist >= 1 << 20

    def test_mission_defaults(self, xb):
        bot = _make_bot(xb, 5, 5)
        m = xb.Mission(bot.tiles[0][0], bot.tiles[1][0], turn=42)
        assert m.target is bot.tiles[0][0]
        assert m.curr_tile is bot.tiles[1][0]
        assert m.last_updated == 42
        assert m.is_removed is False


# ---------------------------------------------------------------------------
# Smoke test: bot can run a tiny game without crashing
# ---------------------------------------------------------------------------
def test_xathis_bot_runs_short_game(tmp_path: Path) -> None:
    """Spawn the (currently stub) bot vs HoldBot for a few turns and verify
    the engine's RESULT line shows up. This guards against import/syntax
    breakage in the scaffold as we add phases later."""

    import subprocess

    cmd = [
        sys.executable, str(REPO_ROOT / "src" / "tools" / "playgame.py"),
        "--player_seed", "1",
        "--end_wait=0.1",
        "--log_dir", str(tmp_path),
        "--turns", "30",
        "--map_file", str(REPO_ROOT / "maps" / "maze" / "maze_02p_01.map"),
        "{0} {1}".format(sys.executable, SRC_BOTS / "xathis_bot.py"),
        "{0} {1}".format(sys.executable, REPO_ROOT / "src" / "sample_bots" / "python" / "HoldBot.py"),
        "--nolaunch",
    ]
    proc = subprocess.run(
        cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, (
        "playgame failed:\nstdout={0}\nstderr={1}".format(proc.stdout[-500:], proc.stderr[-500:])
    )
    assert "RESULT" in proc.stdout, (
        "no RESULT line — xathis_bot probably crashed:\n"
        "stdout={0}\nstderr={1}".format(proc.stdout[-500:], proc.stderr[-500:])
    )
    assert "xathis_bot.py:rank=" in proc.stdout
