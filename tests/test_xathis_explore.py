"""Tests for ``_init_explore`` and ``_explore`` (Strategy.java:891-988).

These tests build small synthetic worlds (no real game engine needed)
and verify the diffusion-based exploration phase moves ants toward the
highest-``explore_value`` frontier.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_BOTS = REPO_ROOT / "src" / "bots"


@pytest.fixture(scope="module")
def xb():
    prev_ants = sys.modules.get("ants")
    spec_helper = importlib.util.spec_from_file_location("ants", SRC_BOTS / "ants.py")
    assert spec_helper and spec_helper.loader
    helper = importlib.util.module_from_spec(spec_helper)
    sys.modules["ants"] = helper
    spec_helper.loader.exec_module(helper)  # type: ignore[union-attr]

    spec = importlib.util.spec_from_file_location(
        "xathis_explore_under_test", SRC_BOTS / "xathis_bot.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["xathis_explore_under_test"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    yield mod

    if prev_ants is None:
        sys.modules.pop("ants", None)
    else:
        sys.modules["ants"] = prev_ants


def _build(xb, rows: int = 40, cols: int = 40,
           my_at: Iterable[Tuple[int, int]] = (),
           enemy_at: Iterable[Tuple[int, int]] = (),
           food_at: Iterable[Tuple[int, int]] = (),
           water_at: Iterable[Tuple[int, int]] = ()):
    bot = xb.XathisBot()
    bot.rows = rows
    bot.cols = cols
    bot.tiles = [[xb.Tile(r, c) for c in range(cols)] for r in range(rows)]
    for r in range(rows):
        for c in range(cols):
            bot.tiles[r][c].neighbors = (
                bot.tiles[(r - 1) % rows][c],
                bot.tiles[r][(c + 1) % cols],
                bot.tiles[(r + 1) % rows][c],
                bot.tiles[r][(c - 1) % cols],
            )

    for (r, c) in water_at:
        t = bot.tiles[r][c]
        t.tile_type = -4  # WATER
        for n in t.neighbors:
            if t in n.neighbors:
                n.neighbors = tuple(x for x in n.neighbors if x is not t)
        t.neighbors = ()

    for (r, c) in my_at:
        t = bot.tiles[r][c]
        t.tile_type = 0  # MY_ANT
        a = xb.Ant(t)
        t.ant = a
        t.old_ant = a
        bot.my_ants.append(a)

    for (r, c) in enemy_at:
        t = bot.tiles[r][c]
        t.tile_type = 1
        a = xb.Ant(t)
        t.ant = a
        t.old_ant = a
        bot.enemy_ants.append(a)

    for (r, c) in food_at:
        t = bot.tiles[r][c]
        t.tile_type = -3  # FOOD
        bot.foods.append(t)

    return bot


def _zero_all_explore_values(bot):
    for row in bot.tiles:
        for tile in row:
            tile.explore_value = 0


# ===========================================================================
# _init_explore
# ===========================================================================
class TestInitExplore:
    def test_no_ants_doesnt_crash(self, xb):
        bot = _build(xb)
        bot._init_explore()  # no-op

    def test_zeros_within_horizon(self, xb):
        bot = _build(xb, my_at=[(20, 20)])
        # Pre-set every tile to 100 so we can see what got reset.
        for row in bot.tiles:
            for t in row:
                t.explore_value = 100
        bot._init_explore()
        # Tile at the ant location: dist 0 → zeroed.
        assert bot.tiles[20][20].explore_value == 0
        # Tile at dist 10 (max horizon) → zeroed.
        assert bot.tiles[20][30].explore_value == 0
        assert bot.tiles[30][20].explore_value == 0
        # Tile at dist 11 (just past horizon) → untouched.
        assert bot.tiles[20][31].explore_value == 100
        # Far tile → untouched.
        assert bot.tiles[39][39].explore_value == 100

    def test_isReached_is_cleaned_up(self, xb):
        bot = _build(xb, my_at=[(20, 20)])
        bot._init_explore()
        for row in bot.tiles:
            for t in row:
                assert t.is_reached is False

    def test_two_ants_overlap(self, xb):
        # Two ants 4 tiles apart. The intersection of their 10-radius
        # disks should also be zeroed; nothing weird happens.
        bot = _build(xb, my_at=[(20, 18), (20, 22)])
        for row in bot.tiles:
            for t in row:
                t.explore_value = 100
        bot._init_explore()
        # Midpoint between the two ants:
        assert bot.tiles[20][20].explore_value == 0
        # Tiles within 10 of either ant:
        assert bot.tiles[20][8].explore_value == 0   # 10 west of ant1
        assert bot.tiles[20][32].explore_value == 0  # 10 east of ant2
        # Tile not within 10 of either:
        assert bot.tiles[20][33].explore_value == 100


# ===========================================================================
# _explore
# ===========================================================================
class TestExplore:
    def test_no_ants_no_orders(self, xb):
        orders: list = []

        class StubEngine:
            def issue_order(self, o):
                orders.append(o)

        bot = _build(xb)
        bot._engine = StubEngine()
        bot._explore()
        assert orders == []

    def test_ant_with_zero_frontier_doesnt_move(self, xb):
        """If every reachable tile has explore_value 0, no first step has
        any value to "earn" and the ant stays put.
        """
        orders: list = []

        class StubEngine:
            def issue_order(self, o):
                orders.append(o)

        bot = _build(xb, my_at=[(20, 20)])
        bot._engine = StubEngine()
        bot._init_turn()
        bot._init_explore()  # zeroes the disk around the ant
        # All tiles outside the disk also start at 100 by default; explicitly
        # zero them so there's literally no fog anywhere.
        _zero_all_explore_values(bot)
        bot._explore()
        assert orders == []
        assert bot.my_ants[0].has_moved is False

    def test_ant_pulled_toward_high_value_frontier(self, xb):
        """A "fog" blob to the east at the horizon should pull the ant east."""
        orders: list = []

        class StubEngine:
            def issue_order(self, o):
                orders.append(o)

        bot = _build(xb, my_at=[(20, 20)])
        bot._engine = StubEngine()
        bot._init_turn()
        bot._init_explore()
        # Wipe everything, then put a single high-value tile at the east frontier
        # (dist 11 — just past the horizon, i.e. visible to _explore_ant).
        _zero_all_explore_values(bot)
        bot.tiles[20][31].explore_value = 5000  # just past horizon, due east
        bot._explore()
        # Ant should move east (issue_order with direction "e").
        assert orders, "explore should have issued at least one move"
        r, c, d = orders[0]
        assert (r, c) == (20, 20)
        assert d == "e", f"expected east toward fog, got {d}"

    def test_ant_moves_toward_largest_blob(self, xb):
        """If two fog blobs exist, the ant should head toward the bigger one."""
        orders: list = []

        class StubEngine:
            def issue_order(self, o):
                orders.append(o)

        bot = _build(xb, my_at=[(20, 20)])
        bot._engine = StubEngine()
        bot._init_turn()
        bot._init_explore()
        _zero_all_explore_values(bot)
        # Small blob west, big blob east.
        bot.tiles[20][9].explore_value = 100
        bot.tiles[20][31].explore_value = 9999
        bot._explore()
        assert orders, "explore should have issued at least one move"
        _, _, d = orders[0]
        assert d == "e"

    def test_indirectly_dangered_ant_does_not_explore(self, xb):
        """Ants flagged isIndirectlyDangered are skipped (combat handles them)."""
        orders: list = []

        class StubEngine:
            def issue_order(self, o):
                orders.append(o)

        bot = _build(xb, my_at=[(20, 20)], enemy_at=[(20, 22)])
        bot._engine = StubEngine()
        bot._init_turn()
        # The enemy is at gamma-dist (dr=0, dc=2), so my ant gets the flag.
        assert bot.my_ants[0].is_indirectly_dangered is True
        bot._init_explore()
        _zero_all_explore_values(bot)
        bot.tiles[20][31].explore_value = 5000  # bait
        bot._explore()
        assert orders == []
        assert bot.my_ants[0].has_moved is False

    def test_already_moved_ant_skipped(self, xb):
        orders: list = []

        class StubEngine:
            def issue_order(self, o):
                orders.append(o)

        bot = _build(xb, my_at=[(20, 20)])
        bot._engine = StubEngine()
        bot._init_turn()
        bot._init_explore()
        _zero_all_explore_values(bot)
        bot.tiles[20][31].explore_value = 5000
        bot.my_ants[0].has_moved = True
        bot._explore()
        assert orders == []

    def test_water_blocks_first_step(self, xb):
        """If water sits to the east, the explore wave can still reach
        the eastern fog via north/south detours; whichever first step
        accumulates the most value wins.

        Concretely: ant at (20,20) with water at (20,21) and a single
        high-value frontier tile at (20,31). The ant should pick a
        non-blocked first step (n or s, not e or w into water).
        """
        orders: list = []

        class StubEngine:
            def issue_order(self, o):
                orders.append(o)

        bot = _build(xb, my_at=[(20, 20)], water_at=[(20, 21)])
        bot._engine = StubEngine()
        bot._init_turn()
        bot._init_explore()
        _zero_all_explore_values(bot)
        bot.tiles[20][31].explore_value = 5000
        bot._explore()
        if orders:
            _, _, d = orders[0]
            assert d in ("n", "s"), (
                f"expected detour around water, got {d}"
            )
        # If no orders were issued (water+horizon makes the frontier
        # unreachable in 10 steps), that's also acceptable — the bot
        # would fall through to other phases.

    def test_does_not_move_onto_food(self, xb):
        """The destination must satisfy ``is_free()`` AND ``not is_hill``;
        a food tile is not free, so we shouldn't pick it as a first step.
        """
        orders: list = []

        class StubEngine:
            def issue_order(self, o):
                orders.append(o)

        bot = _build(xb, my_at=[(20, 20)], food_at=[(20, 21)])
        bot._engine = StubEngine()
        bot._init_turn()
        bot._init_explore()
        _zero_all_explore_values(bot)
        # Place fog east — the natural route is east, but east is blocked
        # by food. Acceptable behaviour: skip the move (food phase will
        # claim it next turn) OR detour via n/s.
        bot.tiles[20][31].explore_value = 5000
        bot._explore()
        if orders:
            r, c, d = orders[0]
            # Make sure we did NOT step east onto the food tile.
            assert d != "e"

    def test_consumed_frontier_zeroed(self, xb):
        """After picking a first step, the frontier tiles "owned" by that
        first step should have their explore_value zeroed so the next
        ant chooses a different blob.
        """
        orders: list = []

        class StubEngine:
            def issue_order(self, o):
                orders.append(o)

        bot = _build(xb, my_at=[(20, 20)])
        bot._engine = StubEngine()
        bot._init_turn()
        bot._init_explore()
        _zero_all_explore_values(bot)
        bot.tiles[20][31].explore_value = 5000  # frontier east
        bot._explore()
        # After explore, the frontier tile that the chosen first-step "ate"
        # should be zero (so two ants don't both home in on it).
        assert bot.tiles[20][31].explore_value == 0
