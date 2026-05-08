"""Tests for ``_enemy_hills`` (Strategy.java:486-514) and
``_defence`` / ``_defend_hill`` (Strategy.java:368-484).
"""

from __future__ import annotations

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
        "xathis_hd_under_test", SRC_BOTS / "xathis_bot.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["xathis_hd_under_test"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    yield mod

    if prev_ants is None:
        sys.modules.pop("ants", None)
    else:
        sys.modules["ants"] = prev_ants


class StubEngine:
    def __init__(self) -> None:
        self.orders: List[Tuple[int, int, str]] = []

    def issue_order(self, order: Tuple[int, int, str]) -> None:
        self.orders.append(order)


def _build(xb, rows: int = 40, cols: int = 40,
           my_at: Iterable[Tuple[int, int]] = (),
           enemy_at: Iterable[Tuple[int, int]] = (),
           food_at: Iterable[Tuple[int, int]] = (),
           water_at: Iterable[Tuple[int, int]] = (),
           my_hills_at: Iterable[Tuple[int, int]] = (),
           enemy_hills_at: Iterable[Tuple[int, int]] = ()):
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
        t.tile_type = -4
        for n in t.neighbors:
            if t in n.neighbors:
                n.neighbors = tuple(x for x in n.neighbors if x is not t)
        t.neighbors = ()

    for (r, c) in my_hills_at:
        t = bot.tiles[r][c]
        t.is_hill = True
        t.hill_player = 0
        bot.my_hills.append(t)

    for (r, c) in enemy_hills_at:
        t = bot.tiles[r][c]
        t.is_hill = True
        t.hill_player = 1
        bot.enemy_hills.append(t)

    for (r, c) in my_at:
        t = bot.tiles[r][c]
        t.tile_type = 0
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
        t.tile_type = -3
        bot.foods.append(t)

    bot._engine = StubEngine()
    return bot


# ===========================================================================
# _enemy_hills
# ===========================================================================
class TestEnemyHills:
    def test_no_enemy_hills_no_orders(self, xb):
        bot = _build(xb, my_at=[(5, 5)])
        bot._init_turn()
        bot._enemy_hills()
        assert bot._engine.orders == []

    def test_single_attacker_when_small_colony(self, xb):
        # 5 ants, 1 enemy hill 4 east. Only 1 attacker should be sent.
        bot = _build(
            xb,
            my_at=[(10, 10), (10, 5), (5, 10), (15, 10), (10, 15)],
            enemy_hills_at=[(10, 14)],
        )
        bot._init_turn()
        bot._enemy_hills()
        # The closest ant is (10,15) at dist 1 — it should move west onto
        # the hill (or to its predecessor on the BFS).
        assert len(bot._engine.orders) == 1
        r, c, d = bot._engine.orders[0]
        assert (r, c) == (10, 15)
        # The BFS predecessor of (10,15) when expanding from (10,14) is
        # (10,14) itself, so we move west onto the hill.
        assert d == "w"

    def test_up_to_4_attackers_when_big_colony(self, xb):
        # 11 ants surrounding an enemy hill. With > 10 ants we send up
        # to 4 attackers.
        my_positions: List[Tuple[int, int]] = [
            (10, 6), (10, 7), (10, 8), (10, 9),  # west of hill
            (10, 11), (10, 12),                   # east of hill
            (9, 10), (8, 10), (7, 10),            # north of hill
            (11, 10), (12, 10),                   # south of hill
        ]
        bot = _build(
            xb,
            my_at=my_positions,
            enemy_hills_at=[(10, 10)],
        )
        bot._init_turn()
        bot._enemy_hills()
        # Up to 4 attackers should have moved.
        assert 1 <= len(bot._engine.orders) <= 4

    def test_does_not_walk_onto_friendly_ant(self, xb):
        # Two ants in a line: the inner one (closer to hill) blocks the
        # outer one's path. Outer ant shouldn't be moved (predecessor is
        # a my-ant tile).
        bot = _build(
            xb,
            my_at=[(10, 11), (10, 12)],   # inner, outer
            enemy_hills_at=[(10, 10)],
        )
        bot._init_turn()
        bot._enemy_hills()
        # Only the inner ant should have moved (one step toward hill).
        moves = bot._engine.orders
        # The inner (10,11) ant moves west onto the hill.
        assert (10, 11, "w") in moves
        # The outer (10,12) ant must NOT have moved west onto its
        # neighbour (which is the inner ant).
        for r, c, d in moves:
            assert not (r == 10 and c == 12 and d == "w"), (
                "outer ant should not walk onto friendly ant tile"
            )

    def test_ant_outside_radius_not_called(self, xb):
        # On a 60x60 torus, hill at (10,10), ant at (10,32). Min torus
        # distance: min(22, 38) = 22 > 20 so the BFS depth-20 horizon
        # does not reach the ant.
        bot = _build(
            xb, rows=60, cols=60,
            my_at=[(10, 32)],
            enemy_hills_at=[(10, 10)],
        )
        bot._init_turn()
        bot._enemy_hills()
        assert bot._engine.orders == []


# ===========================================================================
# _defence
# ===========================================================================
class TestDefence:
    def test_no_hills_no_orders(self, xb):
        bot = _build(xb)
        bot._init_turn()
        bot._defence()
        assert bot._engine.orders == []

    def test_skipped_when_more_than_4_hills(self, xb):
        # 5 my-hills, 1 enemy threatening one of them. Should NOT defend.
        bot = _build(
            xb,
            my_at=[(0, 1)],
            enemy_at=[(0, 4)],
            my_hills_at=[(0, 0), (10, 10), (20, 20), (30, 30), (35, 35)],
        )
        bot._init_turn()
        bot._defence()
        assert bot._engine.orders == []

    def test_defender_intercepts_threat(self, xb):
        # Hill at (10,10), my-ant at (10,11) (defender adjacent), enemy
        # at (10,15). The defender should move east toward the enemy.
        bot = _build(
            xb,
            my_at=[(10, 11)],
            enemy_at=[(10, 15)],
            my_hills_at=[(10, 10)],
        )
        bot._init_turn()
        bot._defence()
        assert len(bot._engine.orders) == 1
        r, c, d = bot._engine.orders[0]
        assert (r, c) == (10, 11)
        # Defender on the path between hill and enemy moves east.
        assert d == "e"

    def test_no_threat_no_orders(self, xb):
        # No enemy ants → no threats → no defender moves.
        bot = _build(
            xb,
            my_at=[(10, 11)],
            my_hills_at=[(10, 10)],
        )
        bot._init_turn()
        bot._defence()
        assert bot._engine.orders == []

    def test_threat_outside_horizon_ignored(self, xb):
        # Enemy 16 tiles from the hill — outside DEFENCE_HORIZON (14).
        bot = _build(
            xb,
            my_at=[(10, 11)],
            enemy_at=[(10, 26)],   # 16 east
            my_hills_at=[(10, 10)],
        )
        bot._init_turn()
        bot._defence()
        assert bot._engine.orders == []
