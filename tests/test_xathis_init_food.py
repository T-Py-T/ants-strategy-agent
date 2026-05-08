"""Tests for ``_init_turn``, the safety gates, and ``_food``.

These three are tested together because ``_food``'s safety logic
(``is_tile_safe2``, ``is_suicide``) reads the gamma-distance adjacency
table that ``_init_turn`` populates. Tests build small synthetic worlds
by directly manipulating tile types — no real game required.
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
        "xathis_init_under_test", SRC_BOTS / "xathis_bot.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["xathis_init_under_test"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    yield mod

    if prev_ants is None:
        sys.modules.pop("ants", None)
    else:
        sys.modules["ants"] = prev_ants


def _build(xb, rows: int = 30, cols: int = 30,
           my_at: Iterable[Tuple[int, int]] = (),
           enemy_at: Iterable[Tuple[int, int]] = (),
           food_at: Iterable[Tuple[int, int]] = (),
           water_at: Iterable[Tuple[int, int]] = ()):
    """Build a XathisBot with fully-set-up tile graph and ant lists."""
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

    # Water
    for (r, c) in water_at:
        t = bot.tiles[r][c]
        t.tile_type = -4  # WATER
        for n in t.neighbors:
            if t in n.neighbors:
                n.neighbors = tuple(x for x in n.neighbors if x is not t)
        t.neighbors = ()

    # Ants
    for (r, c) in my_at:
        t = bot.tiles[r][c]
        t.tile_type = 0  # MY_ANT
        a = xb.Ant(t)
        t.ant = a
        t.old_ant = a
        bot.my_ants.append(a)

    for (r, c) in enemy_at:
        t = bot.tiles[r][c]
        t.tile_type = 1  # PLAYER1
        a = xb.Ant(t)
        t.ant = a
        t.old_ant = a
        bot.enemy_ants.append(a)

    for (r, c) in food_at:
        t = bot.tiles[r][c]
        t.tile_type = -3  # FOOD
        bot.foods.append(t)

    return bot


# ===========================================================================
# _init_turn
# ===========================================================================
class TestInitTurn:
    def test_no_ants_doesnt_crash(self, xb):
        bot = _build(xb)
        bot._init_turn()  # should be no-op without errors

    def test_close_own_ant_pair_count(self, xb):
        bot = _build(xb, my_at=[(5, 5), (5, 7), (15, 15)])
        bot._init_turn()
        # (5,5) and (5,7) are within 5 row + 5 col → close
        # (15,15) is far from both
        a, b, c = bot.my_ants
        assert a.num_close_own_ants == 1
        assert b.num_close_own_ants == 1
        assert c.num_close_own_ants == 0

    def test_close_enemy_dists_populated(self, xb):
        bot = _build(xb, my_at=[(10, 10)], enemy_at=[(10, 12), (10, 13), (20, 20)])
        bot._init_turn()
        my_ant = bot.my_ants[0]
        # (10,12) is dist² = 4, (10,13) = 9; both ≤ 81 (radius 9² = 81)
        # (20,20) = 100+100 = 200 > 81 → excluded
        assert len(my_ant.close_enemy_dists) == 2
        dists = [d for d, _ in my_ant.close_enemy_dists]
        assert dists == [4, 9]
        # closest_enemy_tile should point at the closer enemy (10,12)
        assert my_ant.closest_enemy_tile is bot.tiles[10][12]

    def test_dangered_flag(self, xb):
        # (10,10) and enemy at (12,11): dx=1, dy=2, dx+dy=3 ≤ 4 → dangered
        bot = _build(xb, my_at=[(10, 10)], enemy_at=[(12, 11)])
        bot._init_turn()
        assert bot.my_ants[0].is_dangered is True
        assert bot.my_ants[0].is_indirectly_dangered is True
        assert bot.dangered_ants == [bot.my_ants[0]]

    def test_indirectly_dangered_but_not_dangered(self, xb):
        # gamma but not dangered: dx+dy in (4,5] excluding the two corners.
        # dr=2, dc=3 → dr+dc=5 → gamma yes, dangered no
        bot = _build(xb, my_at=[(10, 10)], enemy_at=[(12, 13)])
        bot._init_turn()
        assert bot.my_ants[0].is_indirectly_dangered is True
        assert bot.my_ants[0].is_dangered is False
        assert bot.dangered_ants == []

    def test_far_enemy_neither_dangered_nor_gamma(self, xb):
        # (10,10) and enemy at (10,18) → dr=0, dc=8 → outside CLOSE_ENEMY_RADIUS
        bot = _build(xb, my_at=[(10, 10)], enemy_at=[(10, 18)])
        bot._init_turn()
        # 0+64=64 ≤ 81 → still in close_enemy_dists, but not gamma
        assert len(bot.my_ants[0].close_enemy_dists) == 1
        assert bot.my_ants[0].is_indirectly_dangered is False
        assert bot.my_ants[0].is_dangered is False
        assert bot.my_ants[0].gamma_dist_enemies == []

    def test_explore_value_aging(self, xb):
        bot = _build(xb)
        # First call increments all tiles by 1 (from initial 100 → 101).
        bot._init_turn()
        assert bot.tiles[5][5].explore_value == 101
        bot._init_turn()
        assert bot.tiles[5][5].explore_value == 102

    def test_will_stay_after_5_static_turns(self, xb):
        # An enemy that's been in the same neighborhood configuration for
        # 5+ turns gets flagged as will_stay = True.
        for turn_count in range(1, 7):
            bot = _build(xb, enemy_at=[(10, 10)])
            # Force the stay_value bookkeeping to look like 5 prior turns.
            bot.tiles[10][10].stay_value = 0  # all neighbors free
            bot.tiles[10][10].stay_turn_count = turn_count - 1
            bot._init_turn()
            if turn_count >= 5:
                assert bot.enemy_ants[0].will_stay is True, (
                    f"expected will_stay at turn_count={turn_count}"
                )
            else:
                assert bot.enemy_ants[0].will_stay is False


# ===========================================================================
# Safety gates
# ===========================================================================
class TestSafetyGates:
    def test_no_enemies_means_safe(self, xb):
        bot = _build(xb, my_at=[(10, 10)])
        bot._init_turn()
        my_ant = bot.my_ants[0]
        for n in my_ant.tile.neighbors:
            assert bot.is_tile_safe(my_ant, n) is True
            assert bot.is_suicide(my_ant, n) is False

    def test_alpha_dist_to_static_enemy_is_unsafe(self, xb):
        # enemy at (10,12), my-ant at (10,10) wants to move east to (10,11).
        # If enemy will_stay (we'll force the flag), (10,11) is alpha-dist
        # from (10,12) → unsafe.
        bot = _build(xb, my_at=[(10, 10)], enemy_at=[(10, 12)])
        bot._init_turn()
        bot.enemy_ants[0].will_stay = True
        my_ant = bot.my_ants[0]
        # gamma_dist_enemies should include the enemy
        assert bot.enemy_ants[0] in my_ant.gamma_dist_enemies
        east = bot.tiles[10][11]
        assert bot.is_tile_safe(my_ant, east) is False
        assert bot.is_tile_safe2(my_ant, east) is bot.enemy_ants[0]

    def test_safe_move_away_from_enemy(self, xb):
        bot = _build(xb, my_at=[(10, 10)], enemy_at=[(10, 12)])
        bot._init_turn()
        bot.enemy_ants[0].will_stay = True
        my_ant = bot.my_ants[0]
        # west takes us further from the static enemy → safe
        west = bot.tiles[10][9]
        assert bot.is_tile_safe(my_ant, west) is True

    def test_suicide_requires_two_threats(self, xb):
        # one static enemy threatening dest → not suicide (1-on-1 wash)
        bot = _build(xb, my_at=[(10, 10)], enemy_at=[(10, 12)])
        bot._init_turn()
        bot.enemy_ants[0].will_stay = True
        my_ant = bot.my_ants[0]
        east = bot.tiles[10][11]
        assert bot.is_suicide(my_ant, east) is False
        # add a SECOND enemy that also threatens (10,11) → suicide
        # enemy at (11,12): alpha-dist to (10,11) is dr=1,dc=1 → yes
        e2_tile = bot.tiles[11][12]
        e2_tile.tile_type = 1
        e2 = xb.Ant(e2_tile)
        e2_tile.ant = e2
        bot.enemy_ants.append(e2)
        # rebuild adjacency
        for a in bot.my_ants:
            a.gamma_dist_enemies = []
            a.is_dangered = False
            a.is_indirectly_dangered = False
            a.close_enemy_dists = []
        bot.dangered_ants = []
        bot._init_turn()
        bot.enemy_ants[0].will_stay = True
        bot.enemy_ants[1].will_stay = True
        assert bot.is_suicide(my_ant, east) is True


# ===========================================================================
# _food
# ===========================================================================
class TestFood:
    def test_no_food_no_crash(self, xb):
        bot = _build(xb, my_at=[(5, 5)])
        bot._init_turn()
        bot._food()
        assert not bot.my_ants[0].has_moved

    def test_single_ant_moves_toward_adjacent_food(self, xb):
        # ant at (5,5), food at (5,8). Multi-source BFS finds my-ant on
        # turn 3 of the wave; ant should move east.
        # Use a stub engine to capture issued orders.
        orders = []

        class StubEngine:
            def issue_order(self, order):
                orders.append(order)

        bot = _build(xb, my_at=[(5, 5)], food_at=[(5, 8)])
        bot._engine = StubEngine()
        bot._init_turn()
        bot._food()
        my_ant = bot.my_ants[0]
        assert my_ant.has_moved is True
        # The wave from food (5,8) reaches (5,5) on dist 3; prev should
        # be (5,6) and the ant moves east.
        assert orders == [(5, 5, "e")]
        assert my_ant.tile.row == 5 and my_ant.tile.col == 6

    def test_two_ants_two_foods_no_collision(self, xb):
        """Multi-source BFS guarantees each food goes to a different ant
        (this is the bug greedy bots have — both ants chase the closer
        food and bunch up)."""

        orders = []

        class StubEngine:
            def issue_order(self, order):
                orders.append(order)

        bot = _build(
            xb,
            my_at=[(5, 5), (5, 20)],
            food_at=[(5, 9), (5, 16)],
        )
        bot._engine = StubEngine()
        bot._init_turn()
        bot._food()
        # ant0 (5,5) is closer to food (5,9) → moves east
        # ant1 (5,20) is closer to food (5,16) → moves west
        # Each food source is consumed when claimed, so we should see
        # exactly 2 orders, one east + one west.
        directions = sorted(o[2] for o in orders)
        assert directions == ["e", "w"]
        assert all(a.has_moved for a in bot.my_ants)

    def test_food_outside_horizon_not_chased(self, xb):
        # food beyond FOOD_BFS_HORIZON should not pull the ant. Use a
        # large enough grid (60x60) that torus-wrap can't make the food
        # accidentally within reach: (5,5) → (5,30) is dist=25 either way.
        bot = _build(xb, rows=60, cols=60, my_at=[(5, 5)], food_at=[(5, 30)])
        orders = []

        class StubEngine:
            def issue_order(self, order):
                orders.append(order)

        bot._engine = StubEngine()
        bot._init_turn()
        bot._food()
        assert orders == []
        assert not bot.my_ants[0].has_moved

    def test_water_blocks_food_path(self, xb):
        # ant at (5,5), food at (5,8), water column at col=6 blocks direct
        # path. Ant must go around (or stay if too far around).
        orders = []

        class StubEngine:
            def issue_order(self, order):
                orders.append(order)

        bot = _build(
            xb,
            my_at=[(5, 5)],
            food_at=[(5, 8)],
            water_at=[(4, 6), (5, 6), (6, 6)],  # full water wall
        )
        bot._engine = StubEngine()
        bot._init_turn()
        bot._food()
        # Ant must go around. Either (4,5) or (6,5) is the first move.
        assert len(orders) <= 1  # wave may reach via long way around or not
        if orders:
            r, c, d = orders[0]
            assert (r, c) == (5, 5)
            assert d in ("n", "s")  # going around the wall


# ===========================================================================
# Off-hill fallback
# ===========================================================================
class TestOffHillFallback:
    def test_idle_ant_on_hill_moves_off(self, xb):
        bot = _build(xb, my_at=[(10, 10)])
        bot.tiles[10][10].is_hill = True
        bot.tiles[10][10].hill_player = 0
        bot.my_hills.append(bot.tiles[10][10])

        orders = []

        class StubEngine:
            def issue_order(self, order):
                orders.append(order)

        bot._engine = StubEngine()
        bot._init_turn()
        bot._off_hill_fallback()
        assert bot.my_ants[0].has_moved is True
        assert len(orders) == 1
        assert orders[0][:2] == (10, 10)

    def test_idle_ant_off_hill_does_not_move(self, xb):
        bot = _build(xb, my_at=[(10, 10)])
        # No hill at (10,10), just an ant standing there.
        bot._init_turn()
        bot._off_hill_fallback()
        assert bot.my_ants[0].has_moved is False
