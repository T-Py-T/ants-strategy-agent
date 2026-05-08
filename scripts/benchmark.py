#!/usr/bin/env python3
"""Run head-to-head benchmarks for the user's bot vs the sample bots.

This replaces the legacy ``scripts/benchmark.sh`` which had a broken
score-parsing path (every game came out as a draw because the shell heredoc
couldn't find ``score`` / ``status`` lines on stdout — they were only being
written to the replay log file).

Usage:
    python3 scripts/benchmark.py                    # default suite
    python3 scripts/benchmark.py --games 10         # more games per matchup
    python3 scripts/benchmark.py --bot foo.py       # alternative bot
    python3 scripts/benchmark.py --map maps/foo.map # single map override

Win/Loss is computed from ``player_0``'s perspective using the engine's
own ranking (``rank`` field of the game result):

* WIN     player_0 has the unique top rank (rank == 0 and no one else does)
* LOSS    player_0 is not at the top rank
* DRAW    multiple players (including player_0) tie for top rank

The script depends on the ``RESULT game_id=...`` line that ``playgame.py``
prints by default; that contract is locked in by ``tests/test_playgame_result_line.py``.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
PLAYGAME = REPO_ROOT / "src" / "tools" / "playgame.py"

RESULT_RE = re.compile(
    r"^RESULT\s+game_id=(?P<game_id>\d+)\s+turns=(?P<turns>\d+)\s+winner=(?P<winner>\S+)\s+(?P<players>.*)$",
    re.MULTILINE,
)

PLAYER_RE = re.compile(
    r"player_(?P<idx>\d+)=(?P<name>[^:]+):rank=(?P<rank>-?\d+),score=(?P<score>-?\d+),status=(?P<status>\S+)"
)


@dataclass
class GameOutcome:
    game_id: int
    turns: int
    winner: str
    players: List[dict]
    duration_s: float
    raw_stdout: str = ""

    @property
    def our_score(self) -> int:
        return int(self.players[0]["score"])

    @property
    def our_status(self) -> str:
        return str(self.players[0]["status"])

    @property
    def our_rank(self) -> int:
        return int(self.players[0]["rank"])

    def outcome_label(self) -> str:
        if "error" in self.winner:
            return "ERROR"
        if self.winner.startswith("tie"):
            return "DRAW" if "player_0" in self.winner else "LOSS"
        return "WIN" if self.winner == "player_0" else "LOSS"


@dataclass
class MatchupSummary:
    name: str
    games: List[GameOutcome] = field(default_factory=list)

    def tally(self) -> dict:
        wins = sum(1 for g in self.games if g.outcome_label() == "WIN")
        losses = sum(1 for g in self.games if g.outcome_label() == "LOSS")
        draws = sum(1 for g in self.games if g.outcome_label() == "DRAW")
        errors = sum(1 for g in self.games if g.outcome_label() == "ERROR")
        n = len(self.games) or 1
        return {
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "errors": errors,
            "win_rate": 100.0 * wins / n,
            "avg_turns": sum(g.turns for g in self.games) / n,
            "avg_time": sum(g.duration_s for g in self.games) / n,
            "avg_our_score": sum(g.our_score for g in self.games) / n,
        }


def parse_result_line(stdout: str) -> Optional[GameOutcome]:
    """Pull the RESULT line out of playgame.py stdout. Returns ``None`` if
    no RESULT line was emitted (e.g. ``--json`` mode or engine crash)."""

    matches = list(RESULT_RE.finditer(stdout))
    if not matches:
        return None
    m = matches[-1]  # last RESULT line in case of multi-round
    players = []
    for pm in PLAYER_RE.finditer(m.group("players")):
        players.append({
            "idx": int(pm.group("idx")),
            "name": pm.group("name"),
            "rank": int(pm.group("rank")),
            "score": int(pm.group("score")),
            "status": pm.group("status"),
        })
    if not players:
        return None
    return GameOutcome(
        game_id=int(m.group("game_id")),
        turns=int(m.group("turns")),
        winner=m.group("winner"),
        players=players,
        duration_s=0.0,  # filled in by caller
    )


def run_one_game(
    *,
    bots: Sequence[str],
    map_file: Path,
    log_dir: Path,
    turns: int,
    seed: int,
    end_wait: float = 0.1,
) -> GameOutcome:
    cmd = [
        sys.executable,
        str(PLAYGAME),
        "--player_seed",
        str(seed),
        "--end_wait={0}".format(end_wait),
        "--log_dir",
        str(log_dir),
        "--turns",
        str(turns),
        "--map_file",
        str(map_file),
        *bots,
        "--nolaunch",
    ]
    t0 = time.monotonic()
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=turns * 2 + 60,
    )
    elapsed = time.monotonic() - t0
    outcome = parse_result_line(proc.stdout)
    if outcome is None:
        # Construct a synthetic ERROR outcome so the suite keeps going.
        outcome = GameOutcome(
            game_id=-1,
            turns=0,
            winner="error",
            players=[{"idx": i, "name": shlex.split(b)[-1], "rank": -1, "score": 0,
                      "status": "no_result"} for i, b in enumerate(bots)],
            duration_s=elapsed,
            raw_stdout=proc.stdout + "\n--- stderr ---\n" + proc.stderr,
        )
    else:
        outcome.duration_s = elapsed
    return outcome


def run_matchup(
    *,
    name: str,
    bots: Sequence[str],
    map_file: Path,
    games: int,
    log_dir: Path,
    turns: int,
    rng: random.Random,
) -> MatchupSummary:
    print("\n[matchup] {0}  ({1} games on {2})".format(name, games, map_file.name))
    summary = MatchupSummary(name=name)
    for i in range(1, games + 1):
        seed = rng.randint(1, 1_000_000)
        outcome = run_one_game(
            bots=bots,
            map_file=map_file,
            log_dir=log_dir,
            turns=turns,
            seed=seed,
        )
        scores = ",".join(str(p["score"]) for p in outcome.players)
        statuses = ",".join(p["status"] for p in outcome.players)
        print(
            "  game {0}/{1}  {2:>5s}  turns={3:<4}  scores=[{4}]  status=[{5}]  ({6:.2f}s)".format(
                i, games, outcome.outcome_label(), outcome.turns, scores, statuses, outcome.duration_s,
            )
        )
        summary.games.append(outcome)
    t = summary.tally()
    print(
        "  → {0} wins / {1} losses / {2} draws / {3} errors  win_rate={4:.0f}%  avg_turns={5:.0f}".format(
            t["wins"], t["losses"], t["draws"], t["errors"], t["win_rate"], t["avg_turns"],
        )
    )
    return summary


def write_summary(summaries: Iterable[MatchupSummary], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    summary_path = output_dir / f"summary_{timestamp}.md"
    json_path = output_dir / f"summary_{timestamp}.json"
    lines = ["# AntsAIBot benchmark summary", "", f"Generated: {timestamp}", ""]
    lines.append("| Matchup | Wins | Losses | Draws | Errors | Win % | Avg turns | Avg time |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    json_blob = []
    for s in summaries:
        t = s.tally()
        lines.append(
            "| {name} | {wins} | {losses} | {draws} | {errors} | {win_rate:.0f}% | {avg_turns:.0f} | {avg_time:.1f}s |".format(
                name=s.name, **t,
            )
        )
        json_blob.append({
            "matchup": s.name,
            "tally": t,
            "games": [{
                "game_id": g.game_id,
                "turns": g.turns,
                "winner": g.winner,
                "outcome": g.outcome_label(),
                "duration_s": g.duration_s,
                "players": g.players,
            } for g in s.games],
        })
    summary_path.write_text("\n".join(lines) + "\n")
    json_path.write_text(json.dumps(json_blob, indent=2) + "\n")
    return summary_path


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Benchmark AntsAIBot vs sample bots.")
    p.add_argument("--bot", default="src/bots/bot.py",
                   help="Path to the bot under test (default: src/bots/bot.py)")
    p.add_argument("--games", type=int, default=5,
                   help="Games per matchup (default: 5)")
    p.add_argument("--turns", type=int, default=1000,
                   help="Maximum turns per game (default: 1000)")
    p.add_argument("--map", default="maps/maze/maze_02p_01.map",
                   help="Map for 2-player matchups")
    p.add_argument("--map-4p", default="maps/maze/maze_04p_01.map",
                   help="Map for the 4-player matchup")
    p.add_argument("--seed", type=int, default=None,
                   help="Master seed for reproducibility (default: random)")
    p.add_argument("--log-dir", default="game_logs",
                   help="Where playgame.py writes per-game replay/log files")
    p.add_argument("--output-dir", default="benchmark_results",
                   help="Where summary markdown and json land")
    p.add_argument("--quick", action="store_true",
                   help="Quick smoke-suite: 2 games per matchup, 200 turns")
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.quick:
        args.games = 2
        args.turns = 200

    rng = random.Random(args.seed)
    bot = "{0} {1}".format(sys.executable, args.bot)
    sample = "{0} src/sample_bots/python".format(sys.executable)

    map_file = (REPO_ROOT / args.map).resolve()
    map_4p = (REPO_ROOT / args.map_4p).resolve()
    log_dir = (REPO_ROOT / args.log_dir).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)

    xathis = "{0} src/bots/xathis_bot.py".format(sys.executable)

    matchups = [
        ("vs_RandomBot", [bot, f"{sample}/RandomBot.py"], map_file),
        ("vs_HoldBot",   [bot, f"{sample}/HoldBot.py"],   map_file),
        ("vs_HunterBot", [bot, f"{sample}/HunterBot.py"], map_file),
        ("vs_GreedyBot", [bot, f"{sample}/GreedyBot.py"], map_file),
        ("vs_LeftyBot",  [bot, f"{sample}/LeftyBot.py"],  map_file),
        # The "final boss": our port of the AI Challenge 2011 winner.
        # Beating xathis_bot is the long-term goal for any ML successor.
        ("vs_XathisBot", [bot, xathis], map_file),
        ("Four_Player",  [bot, f"{sample}/RandomBot.py",
                          f"{sample}/HunterBot.py", f"{sample}/GreedyBot.py"], map_4p),
    ]

    print("AntsAIBot benchmark suite")
    print("=========================")
    print("Bot under test : {0}".format(args.bot))
    print("Games/matchup  : {0}".format(args.games))
    print("Turn limit     : {0}".format(args.turns))
    print("2P map         : {0}".format(args.map))
    print("4P map         : {0}".format(args.map_4p))

    summaries = []
    for name, bots, mp in matchups:
        if not mp.exists():
            print("  [skip] {0}: map not found at {1}".format(name, mp))
            continue
        summaries.append(run_matchup(
            name=name, bots=bots, map_file=mp, games=args.games,
            log_dir=log_dir, turns=args.turns, rng=rng,
        ))

    summary_path = write_summary(summaries, REPO_ROOT / args.output_dir)
    print("\nSummary written to {0}".format(summary_path.relative_to(REPO_ROOT)))

    overall_wins = sum(s.tally()["wins"] for s in summaries)
    overall_total = sum(len(s.games) for s in summaries) or 1
    print("Overall: {0}/{1} wins ({2:.0f}%)".format(
        overall_wins, overall_total, 100.0 * overall_wins / overall_total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
