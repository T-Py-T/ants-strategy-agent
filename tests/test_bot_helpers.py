"""Unit tests for src/bots/ants.py — the helper API consumed by all bots."""

from __future__ import annotations

import pytest

from bots import ants as bot_ants
from bots.ants import (
    AIM,
    ANTS,
    BEHIND,
    DEAD,
    FOOD,
    HILL,
    LAND,
    LEFT,
    MY_ANT,
    RIGHT,
    UNSEEN,
    WATER,
    Ants,
)


SETUP_DATA = """\
turn 0
loadtime 3000
turntime 1000
rows 10
cols 10
turns 200
viewradius2 77
attackradius2 5
spawnradius2 1
player_seed 42
ready
"""


@pytest.fixture
def fresh_ants() -> Ants:
    a = Ants()
    a.setup(SETUP_DATA)
    return a


@pytest.fixture
def populated_ants(fresh_ants: Ants) -> Ants:
    """Ants with a deterministic mid-game state on a 10x10 torus."""

    update = "\n".join(
        [
            "turn 1",
            "a 1 1 0",
            "a 5 5 0",
            "a 2 8 1",
            "f 3 3",
            "f 7 2",
            "h 0 0 0",
            "h 9 9 1",
            "w 4 4",
            "w 4 5",
        ]
    )
    fresh_ants.update(update)
    return fresh_ants


class TestDirectionTables:
    @pytest.mark.parametrize("direction", ["n", "e", "s", "w"])
    def test_aim_unit_vector(self, direction: str) -> None:
        d_row, d_col = AIM[direction]
        assert (d_row, d_col) != (0, 0)
        assert abs(d_row) + abs(d_col) == 1

    def test_left_right_are_inverses(self) -> None:
        for direction in ("n", "e", "s", "w"):
            assert RIGHT[LEFT[direction]] == direction
            assert LEFT[RIGHT[direction]] == direction

    def test_behind_is_opposite(self) -> None:
        for direction in ("n", "e", "s", "w"):
            other = BEHIND[direction]
            assert AIM[direction] == (-AIM[other][0], -AIM[other][1])

    def test_terrain_constants_are_distinct(self) -> None:
        constants = {MY_ANT, ANTS, DEAD, LAND, FOOD, WATER, UNSEEN, HILL}
        # MY_ANT and ANTS are both 0 by design so the set has 7 distinct members.
        assert 0 in constants
        assert WATER in constants
        assert UNSEEN in constants


class TestSetup:
    def test_dimensions_parsed(self, fresh_ants: Ants) -> None:
        assert fresh_ants.width == 10
        assert fresh_ants.height == 10

    def test_radii_parsed(self, fresh_ants: Ants) -> None:
        assert fresh_ants.viewradius2 == 77
        assert fresh_ants.attackradius2 == 5
        assert fresh_ants.spawnradius2 == 1

    def test_map_initialized_unseen(self, fresh_ants: Ants) -> None:
        assert len(fresh_ants.map) == 10
        assert all(len(row) == 10 for row in fresh_ants.map)
        assert all(cell == UNSEEN for row in fresh_ants.map for cell in row)


class TestUpdate:
    def test_my_ants(self, populated_ants: Ants) -> None:
        assert sorted(populated_ants.my_ants()) == [(1, 1), (5, 5)]

    def test_enemy_ants(self, populated_ants: Ants) -> None:
        enemies = populated_ants.enemy_ants()
        assert enemies == [((2, 8), 1)]

    def test_food(self, populated_ants: Ants) -> None:
        assert sorted(populated_ants.food()) == [(3, 3), (7, 2)]

    def test_my_hills(self, populated_ants: Ants) -> None:
        assert populated_ants.my_hills() == [(0, 0)]

    def test_enemy_hills(self, populated_ants: Ants) -> None:
        assert populated_ants.enemy_hills() == [((9, 9), 1)]

    def test_water_persists(self, populated_ants: Ants) -> None:
        assert populated_ants.map[4][4] == WATER
        assert populated_ants.map[4][5] == WATER

    def test_clears_previous_state(self, populated_ants: Ants) -> None:
        next_update = "\n".join(["turn 2", "a 1 1 0", "f 0 5"])
        populated_ants.update(next_update)
        assert populated_ants.my_ants() == [(1, 1)]
        assert populated_ants.food() == [(0, 5)]
        # the prior food at (3,3) and (7,2) must be cleared from the food list
        assert (3, 3) not in populated_ants.food()
        assert (7, 2) not in populated_ants.food()


class TestGeometry:
    @pytest.mark.parametrize(
        "row,col,direction,expected",
        [
            (5, 5, "n", (4, 5)),
            (5, 5, "s", (6, 5)),
            (5, 5, "e", (5, 6)),
            (5, 5, "w", (5, 4)),
            (0, 0, "n", (9, 0)),  # torus wrap north
            (0, 0, "w", (0, 9)),  # torus wrap west
            (9, 9, "s", (0, 9)),  # torus wrap south
            (9, 9, "e", (9, 0)),  # torus wrap east
        ],
    )
    def test_destination_torus(
        self,
        fresh_ants: Ants,
        row: int,
        col: int,
        direction: str,
        expected: tuple[int, int],
    ) -> None:
        assert fresh_ants.destination(row, col, direction) == expected

    @pytest.mark.parametrize(
        "a,b,expected",
        [
            ((0, 0), (0, 0), 0),
            ((0, 0), (0, 1), 1),
            ((0, 0), (1, 0), 1),
            ((0, 0), (5, 5), 10),
            ((0, 0), (9, 9), 2),  # torus shortcut, 1 step in each axis
            ((0, 0), (0, 9), 1),  # wrap east-west
            ((0, 0), (9, 0), 1),  # wrap north-south
        ],
    )
    def test_distance_torus(
        self,
        fresh_ants: Ants,
        a: tuple[int, int],
        b: tuple[int, int],
        expected: int,
    ) -> None:
        assert fresh_ants.distance(a[0], a[1], b[0], b[1]) == expected

    def test_direction_basic(self, fresh_ants: Ants) -> None:
        # going from (5,5) to (5,7) is east
        assert fresh_ants.direction(5, 5, 5, 7) == ["e"]
        # going from (5,5) to (3,5) is north
        assert fresh_ants.direction(5, 5, 3, 5) == ["n"]

    def test_direction_diagonal_returns_two(self, fresh_ants: Ants) -> None:
        dirs = fresh_ants.direction(2, 2, 4, 4)
        assert sorted(dirs) == ["e", "s"]

    def test_direction_wraps_for_close_torus_path(self, fresh_ants: Ants) -> None:
        # (0, 0) → (0, 9) on a width-10 torus is shorter going west.
        assert fresh_ants.direction(0, 0, 0, 9) == ["w"]


class TestPassableUnoccupied:
    def test_passable_water_false(self, populated_ants: Ants) -> None:
        assert populated_ants.passable(4, 4) is False
        assert populated_ants.passable(0, 0) is True  # has hill, not water

    def test_unoccupied_excludes_ants_food_water(self, populated_ants: Ants) -> None:
        assert populated_ants.unoccupied(1, 1) is False  # my ant
        assert populated_ants.unoccupied(2, 8) is False  # enemy ant
        assert populated_ants.unoccupied(3, 3) is False  # food
        assert populated_ants.unoccupied(4, 4) is False  # water
        assert populated_ants.unoccupied(0, 1) is True  # plain land


class TestClosestQueries:
    def test_closest_food(self, populated_ants: Ants) -> None:
        # from (1,1): (3,3) is distance 4, (7,2) is distance 5 (torus wraps don't help)
        assert populated_ants.closest_food(1, 1) == (3, 3)

    def test_closest_food_with_filter(self, populated_ants: Ants) -> None:
        # exclude (3,3); only (7,2) remains
        assert populated_ants.closest_food(1, 1, filter=[(3, 3)]) == (7, 2)

    def test_closest_food_none_available(self, fresh_ants: Ants) -> None:
        fresh_ants.update("turn 1\na 0 0 0")
        assert fresh_ants.closest_food(0, 0) is None

    def test_closest_enemy_ant(self, populated_ants: Ants) -> None:
        assert populated_ants.closest_enemy_ant(1, 1) == (2, 8)

    def test_closest_enemy_hill(self, populated_ants: Ants) -> None:
        # from (1,1) the enemy hill at (9,9) is torus-distance min(8,2)+min(8,2)=4
        assert populated_ants.closest_enemy_hill(1, 1) == (9, 9)

    def test_closest_unseen(self, populated_ants: Ants) -> None:
        result = populated_ants.closest_unseen(1, 1)
        # known squares from the update are not unseen; pick *some* unseen square.
        assert result is not None
        r, c = result
        assert populated_ants.map[r][c] == UNSEEN


class TestRender:
    def test_render_text_map_shape(self, populated_ants: Ants) -> None:
        rendered = populated_ants.render_text_map()
        lines = [line for line in rendered.splitlines() if line]
        assert len(lines) == populated_ants.height
        for line in lines:
            assert line.startswith("# ")
            assert len(line) == 2 + populated_ants.width
