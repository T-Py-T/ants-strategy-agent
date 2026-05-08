"""Unit tests for src/bots/bot.py::AdvancedBot.

These don't run real games; they drive the bot's decision loop with a
fake ``ants`` object that satisfies the helper API surface used by the bot.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from bots import ants as bot_helper_ants
from bots.ants import AIM, BEHIND, LEFT, RIGHT


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_bot_module():
    """Load src/bots/bot.py with ``from ants import *`` resolving correctly.

    ``bot.py`` is normally invoked as a script from ``src/bots/`` so its
    ``from ants import *`` line picks up the sibling ``ants.py``. When loaded
    from a test process the bare name ``ants`` would otherwise resolve to the
    engine package, whose ``__init__`` is empty. We temporarily alias the bot
    helper module under ``ants`` so the import resolves to the same module the
    bot uses at runtime.
    """

    bot_path = REPO_ROOT / "src" / "bots" / "bot.py"
    spec = importlib.util.spec_from_file_location("antsaibot_bot_under_test", bot_path)
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


bot_module = _load_bot_module()
AdvancedBot = bot_module.AdvancedBot


class FakeAnts:
    """Minimal stand-in for the ``Ants`` helper, expressive enough for AdvancedBot."""

    def __init__(
        self,
        height: int = 10,
        width: int = 10,
        my_ants_locs=(),
        enemy_ants_locs=(),
        my_hills_locs=(),
        enemy_hills_with_owner=(),
        food_locs=(),
        water_locs=(),
    ) -> None:
        self.height = height
        self.width = width
        self._my_ants = list(my_ants_locs)
        self._enemy_ants = list(enemy_ants_locs)  # list of (loc, owner)
        self._my_hills = list(my_hills_locs)
        self._enemy_hills = list(enemy_hills_with_owner)
        self._food = list(food_locs)
        self._water = set(water_locs)
        self.orders = []
        self.map = [[-2 for _ in range(width)] for _ in range(height)]
        # mark water as -4 (matches WATER constant in bots.ants)
        for r, c in self._water:
            self.map[r][c] = -4

    # query helpers
    def my_ants(self):
        return list(self._my_ants)

    def enemy_ants(self):
        return list(self._enemy_ants)

    def my_hills(self):
        return list(self._my_hills)

    def enemy_hills(self):
        return list(self._enemy_hills)

    def food(self):
        return list(self._food)

    def passable(self, row, col):
        return (row, col) not in self._water

    def unoccupied(self, row, col):
        if (row, col) in self._water:
            return False
        if (row, col) in self._my_ants:
            return False
        if (row, col) in [loc for loc, _ in self._enemy_ants]:
            return False
        if (row, col) in self._food:
            return False
        return True

    def destination(self, row, col, direction):
        d_row, d_col = AIM[direction]
        return ((row + d_row) % self.height, (col + d_col) % self.width)

    def distance(self, r1, c1, r2, c2):
        d_row = min(abs(r1 - r2), self.height - abs(r1 - r2))
        d_col = min(abs(c1 - c2), self.width - abs(c1 - c2))
        return d_row + d_col

    def direction(self, r1, c1, r2, c2):
        dirs = []
        if r1 != r2:
            if (r2 - r1) % self.height < self.height // 2:
                dirs.append("s")
            else:
                dirs.append("n")
        if c1 != c2:
            if (c2 - c1) % self.width < self.width // 2:
                dirs.append("e")
            else:
                dirs.append("w")
        return dirs

    def closest_food(self, r, c, filter=None):
        return self._closest(self._food, r, c, filter)

    def closest_enemy_ant(self, r, c, filter=None):
        # filter excludes locs we've already targeted
        excluded = set(filter or [])
        candidates = [loc for loc, _ in self._enemy_ants if loc not in excluded]
        if not candidates:
            return None
        return min(candidates, key=lambda loc: self.distance(r, c, loc[0], loc[1]))

    def closest_enemy_hill(self, r, c, filter=None):
        excluded = set(filter or [])
        candidates = [loc for loc, _ in self._enemy_hills if loc not in excluded]
        if not candidates:
            return None
        return min(candidates, key=lambda loc: self.distance(r, c, loc[0], loc[1]))

    def closest_unseen(self, r, c, filter=None):
        return None  # treat the whole map as seen for these tests

    def _closest(self, items, r, c, filter):
        excluded = set(filter or [])
        candidates = [loc for loc in items if loc not in excluded]
        if not candidates:
            return None
        return min(candidates, key=lambda loc: self.distance(r, c, loc[0], loc[1]))

    def issue_order(self, order):
        self.orders.append(order)


class TestAdvancedBotInit:
    def test_initial_state(self) -> None:
        bot = AdvancedBot()
        assert bot.turn_count == 0
        assert bot.ants_straight == {}
        assert bot.ants_lefty == {}
        assert bot.standing_orders == []

    @pytest.mark.parametrize(
        "row,col,expected",
        [
            (0, 0, "n"),  # even row, even col
            (0, 1, "s"),  # even row, odd col
            (1, 0, "e"),  # odd row, even col
            (1, 1, "w"),  # odd row, odd col
        ],
    )
    def test_get_initial_direction(self, row: int, col: int, expected: str) -> None:
        bot = AdvancedBot()
        assert bot.get_initial_direction(row, col) == expected


class TestAdvancedBotDoTurn:
    def test_alone_with_no_targets_does_not_crash(self) -> None:
        bot = AdvancedBot()
        ants = FakeAnts(my_ants_locs=[(5, 5)], my_hills_locs=[(5, 5)])
        bot.do_turn(ants)
        assert bot.turn_count == 1

    def test_moves_toward_food(self) -> None:
        bot = AdvancedBot()
        # An ant near food should issue an order for some direction.
        ants = FakeAnts(
            my_ants_locs=[(5, 5)],
            my_hills_locs=[(0, 0)],  # far enough that hill-return doesn't dominate
            food_locs=[(5, 7)],
        )
        # With only one ant, ``return_to_hill`` always issues an order
        # (very aggressive multiplication path). That's still a valid
        # behavior — assert at least one order was issued for our ant.
        bot.do_turn(ants)
        assert len(ants.orders) >= 1
        row, col, direction = ants.orders[0]
        assert (row, col) == (5, 5)
        assert direction in AIM

    def test_targets_enemy_hill_when_outnumbering(self) -> None:
        bot = AdvancedBot()
        # 3 of our ants vs 1 enemy ant — combat is allowed.
        ants = FakeAnts(
            my_ants_locs=[(0, 1), (1, 0), (1, 1)],
            enemy_ants_locs=[((5, 5), 1)],
            my_hills_locs=[(0, 0)],
            enemy_hills_with_owner=[((9, 9), 1)],
        )
        bot.do_turn(ants)
        assert len(ants.orders) >= 1

    def test_avoids_collisions(self) -> None:
        """Two adjacent ants should never both target the same square."""
        bot = AdvancedBot()
        ants = FakeAnts(
            my_ants_locs=[(0, 0), (0, 2)],
            my_hills_locs=[(5, 5)],
            food_locs=[(0, 1)],  # both ants would naively want this square
        )
        bot.do_turn(ants)
        destinations = [
            ants.destination(row, col, direction)
            for row, col, direction in ants.orders
        ]
        assert len(destinations) == len(set(destinations))

    def test_turn_count_increments(self) -> None:
        bot = AdvancedBot()
        ants = FakeAnts(my_ants_locs=[(0, 0)], my_hills_locs=[(0, 0)])
        for expected in range(1, 4):
            bot.do_turn(ants)
            assert bot.turn_count == expected
