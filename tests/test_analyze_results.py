"""Tests for scripts/analyze_results.py.

These guard against regressions caused by major dependency upgrades
(pandas 3.x, numpy 2.4, scipy 1.17, matplotlib 3.10.x) by exercising the
analyzer end-to-end with both synthetic data and the real
``parallel_statistics.json`` shipped with the repo.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import matplotlib
import pytest

# Use a non-interactive matplotlib backend so plotting never opens a window.
matplotlib.use("Agg")

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_analyzer_module():
    """Import scripts/analyze_results.py by file path (it isn't a package)."""

    path = REPO_ROOT / "scripts" / "analyze_results.py"
    spec = importlib.util.spec_from_file_location("antsaibot_analyze_results", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def analyzer_module():
    return _load_analyzer_module()


@pytest.fixture
def synthetic_results(tmp_path: Path) -> Path:
    payload = [
        {
            "test_name": "vs RandomBot",
            "timestamp": "2026-01-01_00-00-00",
            "games": 4,
            "wins": 3,
            "losses": 1,
            "draws": 0,
            "win_rate": 75.0,
            "average_turns": 250.0,
            "max_parallel": 2,
            "game_results": [
                {
                    "game": 1,
                    "result": "WIN",
                    "our_score": 5,
                    "enemy_score": 1,
                    "turns": 200,
                    "replaydata": {"hive_history": [[0, 0, 5], [0, 0, 1]]},
                },
                {
                    "game": 2,
                    "result": "WIN",
                    "our_score": 4,
                    "enemy_score": 2,
                    "turns": 220,
                    "replaydata": {"hive_history": [[0, 4], [0, 2]]},
                },
                {
                    "game": 3,
                    "result": "WIN",
                    "our_score": 6,
                    "enemy_score": 0,
                    "turns": 230,
                },
                {
                    "game": 4,
                    "result": "LOSS",
                    "our_score": 1,
                    "enemy_score": 5,
                    "turns": 350,
                    # Only one player's hive_history → triggers the "too short" branch
                    "replaydata": {"hive_history": [[1]]},
                },
            ],
        },
        {
            "test_name": "vs HunterBot",
            "timestamp": "2026-01-01_00-00-00",
            "games": 2,
            "wins": 0,
            "losses": 0,
            "draws": 2,
            "win_rate": 0.0,
            "average_turns": 600.0,
            "max_parallel": 2,
            "game_results": [
                {
                    "game": 1,
                    "result": "DRAW",
                    "our_score": 2,
                    "enemy_score": 2,
                    "turns": 600,
                },
                {
                    "game": 2,
                    "result": "DRAW",
                    "our_score": 3,
                    "enemy_score": 3,
                    "turns": 600,
                },
            ],
        },
    ]
    target = tmp_path / "synthetic_stats.json"
    target.write_text(json.dumps(payload))
    return target


class TestAntsAIAnalyzerLoading:
    def test_loads_synthetic_results(self, analyzer_module, synthetic_results: Path) -> None:
        analyzer = analyzer_module.AntsAIAnalyzer(str(synthetic_results))
        assert len(analyzer.df) == 2
        # 4 + 2 game-level rows expected
        assert len(analyzer.game_data) == 6

    def test_food_collected_extracted_from_hive_history(
        self, analyzer_module, synthetic_results: Path
    ) -> None:
        analyzer = analyzer_module.AntsAIAnalyzer(str(synthetic_results))
        random_games = analyzer.game_data[
            analyzer.game_data["test_name"] == "vs RandomBot"
        ]
        # game 1 hive_history was [[0,0,5],[0,0,1]] → food_collected=5, enemy=1
        game1 = random_games[random_games["game"] == 1].iloc[0]
        assert game1["food_collected"] == 5
        assert game1["enemy_food_collected"] == 1
        # game 4 hive_history was too short → both default to 0
        game4 = random_games[random_games["game"] == 4].iloc[0]
        assert game4["food_collected"] == 0
        assert game4["enemy_food_collected"] == 0
        # game 3 had no replaydata → both default to 0
        game3 = random_games[random_games["game"] == 3].iloc[0]
        assert game3["food_collected"] == 0

    def test_missing_file_exits(self, analyzer_module, tmp_path: Path) -> None:
        with pytest.raises(SystemExit):
            analyzer_module.AntsAIAnalyzer(str(tmp_path / "does-not-exist.json"))


class TestAntsAIAnalyzerAnalysis:
    def test_full_analysis_runs(
        self, analyzer_module, synthetic_results: Path, capsys
    ) -> None:
        analyzer = analyzer_module.AntsAIAnalyzer(str(synthetic_results))
        analyzer.full_analysis()
        captured = capsys.readouterr().out
        assert "WIN RATE SUMMARY" in captured
        assert "vs RandomBot" in captured

    def test_performance_trends_runs(
        self, analyzer_module, synthetic_results: Path, capsys
    ) -> None:
        analyzer = analyzer_module.AntsAIAnalyzer(str(synthetic_results))
        # Below the 10-game threshold no per-bucket print happens, but the
        # call should still complete without raising.
        analyzer.performance_trends()

    def test_statistical_significance_runs(
        self, analyzer_module, synthetic_results: Path, capsys
    ) -> None:
        analyzer = analyzer_module.AntsAIAnalyzer(str(synthetic_results))
        analyzer.statistical_significance()
        captured = capsys.readouterr().out
        assert "STATISTICAL SIGNIFICANCE" in captured
        assert "P-value" in captured

    def test_export_detailed_report(
        self, analyzer_module, synthetic_results: Path, tmp_path: Path
    ) -> None:
        analyzer = analyzer_module.AntsAIAnalyzer(str(synthetic_results))
        out_file = tmp_path / "report.json"
        analyzer.export_detailed_report(str(out_file))
        assert out_file.exists()
        report = json.loads(out_file.read_text())
        assert report["total_tests"] == 2
        assert report["total_games"] == 6
        assert "summary" in report
        assert "game_level_analysis" in report

    def test_plot_performance_writes_file(
        self,
        analyzer_module,
        synthetic_results: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # The analyzer always writes ``performance_analysis.png`` in cwd; sandbox it.
        monkeypatch.chdir(tmp_path)
        analyzer = analyzer_module.AntsAIAnalyzer(str(synthetic_results))
        analyzer.plot_performance(save_plots=True)
        assert (tmp_path / "performance_analysis.png").exists()


class TestAgainstBundledStats:
    def test_real_parallel_statistics_loads(self, analyzer_module) -> None:
        path = REPO_ROOT / "parallel_statistics.json"
        if not path.exists():
            pytest.skip("parallel_statistics.json not present in this checkout")
        analyzer = analyzer_module.AntsAIAnalyzer(str(path))
        # The bundled file has 4 test-level rows but no game_results.
        assert len(analyzer.df) >= 1
        # Should not crash even though game_data is empty.
        analyzer.full_analysis()
