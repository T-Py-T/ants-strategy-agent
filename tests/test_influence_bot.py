"""Characterization tests for the recovered influence-map strategy."""

# The protocol double intentionally exposes a broad, method-shaped fixture API.
# pylint: disable=missing-function-docstring,too-many-arguments,too-many-instance-attributes

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from bots import ants as bot_helper_ants
from bots.ants import AIM, FOOD, LAND, WATER

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_bot_module():
    bot_path = REPO_ROOT / "src" / "bots" / "influence_bot.py"
    spec = importlib.util.spec_from_file_location(
        "ants_influence_bot_under_test", bot_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    saved = sys.modules.get("ants")
    sys.modules["ants"] = bot_helper_ants
    try:
        spec.loader.exec_module(module)
    finally:
        if saved is not None:
            sys.modules["ants"] = saved
        else:
            del sys.modules["ants"]
    return module


influence_module = _load_bot_module()
InfluenceBot = influence_module.InfluenceBot


class FakeAnts:
    """Current helper API surface used by the historical strategy adapter."""

    def __init__(
        self,
        *,
        height=15,
        width=15,
        viewradius2=5,
        my_ants=(),
        enemy_ants=(),
        my_hills=(),
        enemy_hills=(),
        food=(),
        water=(),
    ):
        self.height = height
        self.width = width
        self.viewradius2 = viewradius2
        self._my_ants = list(my_ants)
        self._enemy_ants = list(enemy_ants)
        self._my_hills = list(my_hills)
        self._enemy_hills = list(enemy_hills)
        self._food = list(food)
        self.my_ants_calls = 0
        self.orders = []
        self.map = [[LAND for _ in range(width)] for _ in range(height)]
        for row, col in water:
            self.map[row][col] = WATER
        for row, col in self._food:
            self.map[row][col] = FOOD
        for row, col in self._my_ants:
            self.map[row][col] = 0
        for (row, col), owner in self._enemy_ants:
            self.map[row][col] = owner

    def my_ants(self):
        self.my_ants_calls += 1
        return list(self._my_ants)

    def enemy_ants(self):
        return list(self._enemy_ants)

    def my_hills(self):
        return list(self._my_hills)

    def enemy_hills(self):
        return list(self._enemy_hills)

    def food(self):
        return list(self._food)

    def distance(self, row1, col1, row2, col2):
        row_delta = min(abs(row1 - row2), self.height - abs(row1 - row2))
        col_delta = min(abs(col1 - col2), self.width - abs(col1 - col2))
        return row_delta + col_delta

    def destination(self, row, col, direction):
        row_delta, col_delta = AIM[direction]
        return ((row + row_delta) % self.height, (col + col_delta) % self.width)

    def issue_order(self, order):
        self.orders.append(order)


def test_descriptive_alias_keeps_historical_class_identity() -> None:
    assert (
        influence_module.InfluenceBot
        is influence_module.IForOneWelcomeOurNewInsectOverlords
    )


def test_visibility_age_resets_inside_current_vision_circle() -> None:
    ants = FakeAnts(
        height=9,
        width=9,
        viewradius2=1,
        my_ants=[(4, 4), (0, 0)],
    )
    bot = InfluenceBot()
    bot.do_setup(ants)
    bot.visibility_map = [[5 for _ in range(9)] for _ in range(9)]

    bot.update_visibility(ants.my_ants())

    assert bot.visibility_map[4][4] == 0
    assert bot.visibility_map[3][4] == 0
    assert bot.visibility_map[4][5] == 0
    assert bot.visibility_map[8][0] == 0
    assert bot.visibility_map[0][8] == 0
    assert bot.visibility_map[2][4] == 6
    assert ants.my_ants_calls == 1


def test_food_influence_moves_an_ant_toward_collection_range() -> None:
    ants = FakeAnts(
        my_ants=[(7, 7)],
        my_hills=[(7, 7)],
        food=[(7, 9)],
    )
    bot = InfluenceBot()

    bot.do_turn(ants)

    assert ants.orders == [(7, 7, "e")]
    assert ants.map[7][7] == 0, "strategy markers must not mutate protocol state"
    assert ants.map[7][9] == FOOD


def test_tied_influences_preserve_historical_stay_choice() -> None:
    ants = FakeAnts(my_ants=[(7, 7)], my_hills=[(7, 7)])
    bot = InfluenceBot()

    bot.do_turn(ants)

    assert not ants.orders
    assert ants.my_ants_calls == 1


def test_stale_visibility_edges_become_exploration_targets() -> None:
    ants = FakeAnts(
        height=15,
        width=15,
        viewradius2=5,
        my_ants=[(7, 7)],
        my_hills=[(7, 7)],
    )
    bot = InfluenceBot()
    bot.do_setup(ants)
    bot.visibility_map = [[6 for _ in range(15)] for _ in range(15)]
    bot.update_visibility(ants.my_ants())

    edges = bot.edge_locs(ants.my_ants(), ants)

    assert edges
    assert all(bot.visibility_map[row][col] >= 5 for row, col in edges)


def test_orders_reserve_unique_destinations() -> None:
    ants = FakeAnts(
        my_ants=[(7, 6), (7, 8)],
        my_hills=[(7, 7)],
        food=[(5, 7)],
    )
    bot = InfluenceBot()

    bot.do_turn(ants)

    destinations = [
        ants.destination(row, col, direction) for row, col, direction in ants.orders
    ]
    assert len(destinations) == len(set(destinations))
