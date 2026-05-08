"""Unit tests for the engine map-parser in src/ants/ants.py.

We avoid constructing a full Ants engine instance (which requires a substantial
options dict and runs heavy initialization). Instead we exercise the
``parse_map`` method through a lightweight stub that supplies the only
attribute it touches (``scenario``).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ants.ants import Ants


def _parse(map_text: str, *, scenario: bool = False):
    stub = SimpleNamespace(scenario=scenario)
    return Ants.parse_map(stub, map_text)


SIMPLE_MAP = """\
rows 4
cols 6
players 2
m 0....1
m ......
m ..%%..
m ......
"""


class TestParseMapBasics:
    def test_dimensions_and_player_count(self) -> None:
        data = _parse(SIMPLE_MAP)
        assert data["size"] == (4, 6)
        assert data["num_players"] == 2

    def test_hills(self) -> None:
        data = _parse(SIMPLE_MAP)
        assert data["hills"][0] == [(0, 0)]
        assert data["hills"][1] == [(0, 5)]

    def test_water(self) -> None:
        data = _parse(SIMPLE_MAP)
        assert sorted(data["water"]) == [(2, 2), (2, 3)]

    def test_no_food_or_ants_in_simple_map(self) -> None:
        data = _parse(SIMPLE_MAP)
        assert data["food"] == []
        assert data["ants"] == {}


SCENARIO_MAP = """\
rows 3
cols 5
players 2
m 0a..1
m ..*..
m b...A
"""


class TestParseMapScenario:
    def test_scenario_ants_per_player(self) -> None:
        data = _parse(SCENARIO_MAP, scenario=True)
        # 'a' at (0,1) and 'A' (hill+ant) at (2,4) belong to player 0.
        assert sorted(data["ants"][0]) == [(0, 1), (2, 4)]
        assert data["ants"][1] == [(2, 0)]

    def test_scenario_hill_with_ant(self) -> None:
        data = _parse(SCENARIO_MAP, scenario=True)
        # 'A' is hill+ant for player 0
        assert (2, 4) in data["hills"][0]
        assert (2, 4) in data["ants"][0]

    def test_scenario_food(self) -> None:
        data = _parse(SCENARIO_MAP, scenario=True)
        assert data["food"] == [(1, 2)]


class TestParseMapErrors:
    def test_invalid_character(self) -> None:
        bad = "rows 1\ncols 3\nplayers 2\nm 0Z1\n"
        with pytest.raises(Exception, match="Invalid character"):
            _parse(bad, scenario=True)

    def test_player_count_out_of_range(self) -> None:
        bad = "rows 1\ncols 1\nplayers 1\nm .\n"
        with pytest.raises(Exception, match="player count"):
            _parse(bad)

    def test_row_count_mismatch(self) -> None:
        bad = "rows 4\ncols 3\nplayers 2\nm 0.1\nm ...\n"
        with pytest.raises(Exception, match="Incorrect number of rows"):
            _parse(bad)

    def test_col_count_mismatch(self) -> None:
        bad = "rows 1\ncols 5\nplayers 2\nm 0.1\n"
        with pytest.raises(Exception, match="Incorrect number of cols"):
            _parse(bad)

    def test_players_required_before_map_lines(self) -> None:
        bad = "rows 1\ncols 1\nm 0\n"
        with pytest.raises(Exception, match="players count expected"):
            _parse(bad)


class TestParseMapBundledMaps:
    """Smoke-test the parser against actual maps shipped with the repo."""

    @pytest.mark.parametrize(
        "rel_path",
        [
            "maps/example/tutorial1.map",
            "maps/maze/maze_02p_01.map",
            "maps/maze/maze_04p_01.map",
        ],
    )
    def test_real_map_parses(self, rel_path: str) -> None:
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[1]
        map_text = (repo_root / rel_path).read_text()
        data = _parse(map_text)
        height, width = data["size"]
        assert height > 0 and width > 0
        assert data["num_players"] >= 2
        assert len(data["hills"]) == data["num_players"]
        assert all(data["hills"][p] for p in range(data["num_players"]))
