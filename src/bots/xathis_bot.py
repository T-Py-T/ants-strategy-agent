#!/usr/bin/env python
"""XathisBot — a Python port of the AI Challenge 2011 winning bot.

The original is in ``docs/reference/xathis/Strategy.java`` (1,773 lines) and
the postmortem is at ``docs/reference/xathis/postmortem.txt``.

This is V1: scaffolding only. It puts the full data model in place
(``Tile`` / ``Ant`` / torus geometry / combat distances) and the empty
phase ladder from ``Strategy.actions()``. Every phase is a stub that
returns immediately; the bot falls back to a trivial "all ants stay
put" behaviour so it never crashes the engine.

Subsequent commits fill in one phase at a time, in this order:

    initTurn        bookkeeping, dangered/willStay flags, gammaDistEnemies
    food            multi-source BFS from food tiles
    enemyHills      BFS from enemy hills, send up to 4 attackers
    explore         exploreValue diffusion + 11-step BFS
    createAreas     territory flood-fill + border tiles
    fight           gamma-group minimax (the killer feature)
    defence         hill defender interception
    missions        long-running goals to border tiles
    escape          dangered-ant safe-tile lookahead

Each phase added is independently testable; the bot stays playable at
every step.

Reference: ``docs/reference/xathis/Strategy.java`` line numbers are cited
in the docstring of each ported method.
"""

from __future__ import annotations

import sys
import time
from collections import deque
from typing import Deque, Dict, List, Optional, Set, Tuple

# Reuse the shared helper API for stdio + map state. Constants we use:
#   MY_ANT (0), LAND (-2), FOOD (-3), WATER (-4), UNSEEN (-5), HILL (-6)
#   AIM = {'n': (-1, 0), ...}
from ants import (  # type: ignore[import-not-found]
    AIM,
    ANTS,
    DEAD,
    FOOD,
    HILL,
    LAND,
    MY_ANT,
    UNSEEN,
    WATER,
    Ants,
)


# ---------------------------------------------------------------------------
# Tunable constants (lifted directly from Strategy.java)
# ---------------------------------------------------------------------------
# CLOSE_ENEMY_RADIUS — Strategy.java:21
CLOSE_ENEMY_RADIUS: int = 9
CLOSE_ENEMY_RADIUS2: int = CLOSE_ENEMY_RADIUS ** 2

# AREA_DIST — Strategy.java:23
AREA_DIST: int = 20

# Time budget per turn, in ms; xathis sets isTimeout at 420ms and the engine
# default turntime is 500ms. We keep the same headroom.
TURN_TIME_BUDGET_MS: int = 420

# Hill defence horizon — Strategy.java:389
DEFENCE_HORIZON: int = 14

# Food BFS horizon — Strategy.java:572
FOOD_BFS_HORIZON: int = 13

# Explore BFS horizon — Strategy.java:944
EXPLORE_BFS_HORIZON: int = 11

# Escape BFS horizon — Strategy.java:599
ESCAPE_CHECK_DIST: int = 8

# Group-fight cap (per side). xathis uses dependency tables + prec-grouping
# to handle larger groups; we cap at 4 ants per side and exhaustive-search.
# Larger groups fall through to the safety gates and the rest of the ladder.
FIGHT_GROUP_CAP: int = 4

# Hard ceiling on the (my_options × enemy_options) product. Even with
# group cap = 4, a fully-mobile 4v4 fight can hit 5^4 * 5^4 = 390 625
# combinations; we fall through past this to keep turn time predictable.
FIGHT_BRANCHING_CAP: int = 200_000


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
class Tile:
    """A single map cell. Persisted across turns; mutable.

    Mirrors ``docs/reference/xathis/Tile.java``. Many fields are scratch
    space for various BFS passes; we reset them between phases via the
    standard ``isReached`` / ``changedTiles`` pattern.
    """

    __slots__ = (
        "row", "col", "tile_type",
        "ant", "old_ant",
        "neighbors",
        "is_hill", "hill_player",
        # bfs scratch (not reset between turns)
        "dist", "hill_dist", "prev",
        "is_reached",
        # food bfs
        "source",
        # explore
        "explore_value", "prev_firsts", "has_new_land",
        # A*
        "f",
        # distribute
        "is_reached_by_me",
        # combat simulation
        "has_virt_ant",
        # areas
        "start_tile", "is_in_my_area", "is_border",
        # willStay detection
        "stay_turn_count", "stay_value",
        # dep tables
        "is_checked",
    )

    def __init__(self, row: int, col: int) -> None:
        self.row = row
        self.col = col
        self.tile_type: int = LAND
        self.ant: Optional["Ant"] = None
        self.old_ant: Optional["Ant"] = None
        self.neighbors: Tuple["Tile", ...] = ()
        self.is_hill: bool = False
        self.hill_player: int = -1
        self.dist: int = 0
        self.hill_dist: int = 1 << 30
        self.prev: Optional["Tile"] = None
        self.is_reached: bool = False
        self.source: Optional["Tile"] = None
        self.explore_value: int = 100
        self.prev_firsts: Set["Tile"] = set()
        self.has_new_land: bool = False
        self.f: int = 0
        self.is_reached_by_me: bool = False
        self.has_virt_ant: bool = False
        self.start_tile: Optional["Tile"] = None
        self.is_in_my_area: bool = False
        self.is_border: bool = False
        self.stay_turn_count: int = 0
        self.stay_value: int = -1
        self.is_checked: bool = False

    def is_free(self) -> bool:
        """True if this tile is land (not water, food, ant, or hill).

        Mirrors ``Type.isFree()`` (Strategy.java references) — note that
        in the Java version 'free' means LAND specifically, and food /
        hills / ants are considered occupied.
        """
        return self.tile_type == LAND

    def is_enemy(self) -> bool:
        return self.tile_type > MY_ANT  # players 1..9

    def dir_to(self, other: "Tile") -> str:
        """Return the cardinal direction ('n'/'e'/'s'/'w') from this tile
        to a *direct* neighbor, accounting for torus wrap.

        Mirrors ``Tile.dirTo`` (Tile.java:55).
        """
        if other.row == self.row:
            if other.col == self.col + 1:
                return "e"
            if other.col == self.col - 1:
                return "w"
            # wrapped
            return "w" if self.col == 0 else "e"
        if other.row == self.row + 1:
            return "s"
        if other.row == self.row - 1:
            return "n"
        return "n" if self.row == 0 else "s"

    def __repr__(self) -> str:
        return f"Tile({self.row},{self.col})"


class Ant:
    """An ant; lives one turn. Mirrors ``docs/reference/xathis/Ant.java``."""

    __slots__ = (
        "tile",
        "is_dangered", "is_indirectly_dangered",
        "has_moved", "has_mission",
        "is_detached",
        "close_enemy_dists",     # list[(dist2, Ant)] sorted
        "closest_enemy_tile",
        "close_enemy_dists_sum",
        "closest_enemy",
        "closest_enemy_dist",
        "num_close_enemies",
        "gamma_dist_enemies",    # list[Ant]
        "is_dead", "weakness",
        "is_reached", "is_grouped", "is_gamma_grouped",
        "curr_to", "best_to",
        "comp_value",
        "mission",
        "num_close_own_ants",
        "will_stay",
        "dep_table",
        "check_all", "check_neighbors",
        "dist_map",
    )

    def __init__(self, tile: Tile) -> None:
        self.tile: Tile = tile
        self.is_dangered: bool = False
        self.is_indirectly_dangered: bool = False
        self.has_moved: bool = False
        self.has_mission: bool = False
        self.is_detached: bool = True
        self.close_enemy_dists: List[Tuple[int, "Ant"]] = []
        self.closest_enemy_tile: Optional[Tile] = None
        self.close_enemy_dists_sum: int = 0
        self.closest_enemy: Optional["Ant"] = None
        self.closest_enemy_dist: int = 1 << 30
        self.num_close_enemies: int = 0
        self.gamma_dist_enemies: List["Ant"] = []
        self.is_dead: bool = False
        self.weakness: int = 0
        self.is_reached: bool = False
        self.is_grouped: bool = False
        self.is_gamma_grouped: bool = False
        self.curr_to: Optional[Tile] = None
        self.best_to: Optional[Tile] = None
        self.comp_value: int = 0
        self.mission: Optional["Mission"] = None
        self.num_close_own_ants: int = 0
        self.will_stay: bool = False
        self.dep_table: Optional[Dict[Tile, List[Tile]]] = None
        self.check_all: bool = False
        self.check_neighbors: List[Tile] = []
        self.dist_map: Optional[Dict[Tile, int]] = None

    def __repr__(self) -> str:
        return f"Ant({self.tile.row},{self.tile.col})"


class Mission:
    """A long-running goal: an ant heading toward a target tile.

    Mirrors ``Strategy.Mission`` (Strategy.java:256). Persists across
    turns; the path is recomputed via A* every time.
    """

    __slots__ = ("target", "curr_tile", "last_updated", "is_removed")

    def __init__(self, target: Tile, curr_tile: Tile, turn: int) -> None:
        self.target: Tile = target
        self.curr_tile: Tile = curr_tile
        self.last_updated: int = turn
        self.is_removed: bool = False


# ---------------------------------------------------------------------------
# XathisBot
# ---------------------------------------------------------------------------
class XathisBot:
    """Faithful Python port of xathis's AI Challenge 2011 winning bot.

    Used as the "final boss" opponent for AdvancedBot and future
    ML-driven variants in this repo.

    The phase ladder in ``do_turn`` mirrors ``Strategy.actions()``
    (Strategy.java:203). Each phase is one method on this class; phases
    not yet implemented are no-ops that fall through.
    """

    def __init__(self) -> None:
        # Persistent state across turns. Tiles are created lazily on the
        # first do_turn (we need rows/cols from the engine).
        self.rows: int = 0
        self.cols: int = 0
        self.tiles: List[List[Tile]] = []
        self.turn: int = 0
        self.start_time_ms: float = 0.0
        self.is_timeout: bool = False

        # Per-turn data (rebuilt each turn from the engine state).
        self.my_ants: List[Ant] = []
        self.enemy_ants: List[Ant] = []
        self.foods: List[Tile] = []
        self.my_hills: List[Tile] = []
        self.enemy_hills: List[Tile] = []
        self.dangered_ants: List[Ant] = []

        # Long-running missions (persist across turns).
        self.missions: List[Mission] = []

    # ------------------------------------------------------------------
    # Initialization (called on first turn once we know map dimensions)
    # ------------------------------------------------------------------
    def _ensure_initialized(self, ants: Ants) -> None:
        if self.tiles:
            return
        self.rows = ants.height
        self.cols = ants.width
        self.tiles = [[Tile(r, c) for c in range(self.cols)] for r in range(self.rows)]
        # Precompute neighbors. We don't yet know which tiles are water
        # (UNSEEN starts everywhere); we'll prune water neighbors lazily
        # when we encounter them in update_map_state. For now every tile
        # has 4 cardinal neighbors with torus wrap.
        for r in range(self.rows):
            for c in range(self.cols):
                tile = self.tiles[r][c]
                tile.neighbors = (
                    self.tiles[(r - 1) % self.rows][c],   # n
                    self.tiles[r][(c + 1) % self.cols],   # e
                    self.tiles[(r + 1) % self.rows][c],   # s
                    self.tiles[r][(c - 1) % self.cols],   # w
                )

    def _prune_water_neighbors(self, ants: Ants) -> None:
        """Mark known-water tiles and prune them from neighbors lists.

        xathis treats water as a permanent edge in the navigation graph;
        the original ``Tile.removeNeighbor`` (Tile.java:67) is called
        once per tile when water is first observed.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                if ants.map[r][c] == WATER:
                    tile = self.tiles[r][c]
                    if tile.tile_type != WATER:
                        tile.tile_type = WATER
                        # Remove this tile from each of its (former) neighbors.
                        for n in tile.neighbors:
                            if tile in n.neighbors:
                                n.neighbors = tuple(x for x in n.neighbors if x is not tile)
                        tile.neighbors = ()

    # ------------------------------------------------------------------
    # Torus geometry
    # ------------------------------------------------------------------
    def dist_row(self, t1: Tile, t2: Tile) -> int:
        d = abs(t1.row - t2.row)
        return min(d, self.rows - d)

    def dist_col(self, t1: Tile, t2: Tile) -> int:
        d = abs(t1.col - t2.col)
        return min(d, self.cols - d)

    def dist(self, t1: Tile, t2: Tile) -> int:
        """Manhattan distance on the torus (Strategy.java:1752)."""
        return self.dist_row(t1, t2) + self.dist_col(t1, t2)

    # ------------------------------------------------------------------
    # Combat distances (alpha < beta < gamma)
    # ------------------------------------------------------------------
    # The Ants AI Challenge attack rule: an ant dies if any enemy is within
    # ``attackradius2`` Euclidean squared distance (5 by default — i.e.
    # Manhattan d=2 on cardinal axes, d=2 on diagonals up to (1,2)).
    #
    # alpha = "could attack right now"
    # beta  = "could attack next turn after one move (incl. me staying)"
    # gamma = "could attack within two moves"
    #
    # These match Strategy.java:1726, 1732, 1742 exactly.
    def is_alpha_dist(self, t1: Tile, t2: Tile) -> bool:
        dr = self.dist_row(t1, t2)
        dc = self.dist_col(t1, t2)
        return (dc <= 1 and dr <= 2) or (dc == 2 and dr <= 1)

    def is_beta_dist(self, t1: Tile, t2: Tile) -> bool:
        dr = self.dist_row(t1, t2)
        dc = self.dist_col(t1, t2)
        if dr + dc <= 4:
            if (dr == 0 and dc == 4) or (dc == 0 and dr == 4):
                return False
            return True
        return False

    def is_gamma_dist(self, t1: Tile, t2: Tile) -> bool:
        dr = self.dist_row(t1, t2)
        dc = self.dist_col(t1, t2)
        if dr + dc <= 5:
            if (dr == 0 and dc == 5) or (dc == 0 and dr == 5):
                return False
            return True
        return False

    # ------------------------------------------------------------------
    # Main turn entry point
    # ------------------------------------------------------------------
    def do_turn(self, ants: Ants) -> None:
        self.start_time_ms = time.monotonic() * 1000.0
        self.turn += 1
        self._ensure_initialized(ants)
        self._prune_water_neighbors(ants)
        self._sync_engine_state(ants)
        self._actions(ants)

    def _sync_engine_state(self, ants: Ants) -> None:
        """Mirror the Ants engine's view of the world onto our Tile graph.

        Called every turn. xathis's ``Connection`` (Connection.java) does
        equivalent work after each engine update.
        """
        # Reset per-turn flags on tiles. Persistent fields (explore_value,
        # neighbors, is_hill, etc.) are not touched here.
        for row in self.tiles:
            for tile in row:
                if tile.tile_type != WATER:  # keep water permanent
                    tile.tile_type = LAND
                tile.ant = None
                tile.old_ant = None

        # Refresh ant / food / hill positions.
        self.my_ants = []
        self.enemy_ants = []
        self.foods = []
        self.my_hills = []
        self.enemy_hills = []
        self.dangered_ants = []

        for (r, c), owner in ants.ant_list.items():
            tile = self.tiles[r][c]
            tile.tile_type = owner  # 0 = me, 1..9 = enemy player N
            ant = Ant(tile)
            tile.ant = ant
            tile.old_ant = ant
            if owner == MY_ANT:
                self.my_ants.append(ant)
            else:
                self.enemy_ants.append(ant)

        for (r, c) in ants.food_list:
            tile = self.tiles[r][c]
            if tile.tile_type == LAND:  # don't override an ant on the food
                tile.tile_type = FOOD
            self.foods.append(tile)

        for (r, c), owner in ants.hill_list.items():
            tile = self.tiles[r][c]
            tile.is_hill = True
            tile.hill_player = owner
            if owner == MY_ANT:
                self.my_hills.append(tile)
            else:
                self.enemy_hills.append(tile)

        # Stash the engine reference so do_move can call issue_order.
        self._engine = ants

    # ------------------------------------------------------------------
    # Phase ladder (Strategy.java:203)
    # ------------------------------------------------------------------
    def _actions(self, ants: Ants) -> None:
        # Phases marked TODO are stubs; they'll be filled in commit by
        # commit. The order matches Strategy.actions() exactly.
        self._init_turn()
        self._calc_num_close_enemies()
        self._init_missions()
        self._enemy_hills()
        self._food()
        self._init_explore()
        self._create_areas()
        self._fight()
        self._defence()
        self._approach_enemies()
        self._attack_detached_enemies()
        self._escape_enemies()
        self._distribute(only_near_enemy=True)
        self._explore()
        self._do_missions()
        self._create_missions()
        self._distribute(only_near_enemy=False)
        self._clean_areas()
        # Final fallback: ants still sitting on our hill block new spawns.
        # This is a minimal stand-in for `distribute()` until that phase
        # lands; without it the colony plateaus at 1–2 ants because the
        # hill stays occupied. xathis's full distribute (Strategy.java:990)
        # is much smarter — it spreads ants by maximizing reachable tiles.
        self._off_hill_fallback()

    def _off_hill_fallback(self) -> None:
        """Move any my-ant that's still on a my-hill and has no orders to
        a free, safe neighbor. Keeps the spawn pipeline unblocked until
        the real ``distribute`` / ``explore`` phases land.
        """
        my_hill_set = {h for h in self.my_hills}
        for ant in self.my_ants:
            if ant.has_moved or ant.tile not in my_hill_set:
                continue
            for n in ant.tile.neighbors:
                if n.is_free() and not n.is_hill and self.is_tile_safe(ant, n):
                    self.do_move(ant.tile, n, "off-hill")
                    break

    # ------------------------------------------------------------------
    # Phase: _init_turn (Strategy.java:78-202)
    # ------------------------------------------------------------------
    def _init_turn(self) -> None:
        """Per-turn precomputation: close-ant pair counts, close-enemy
        distances, dangered/indirectly-dangered flags, gamma-distance
        adjacency, ``willStay`` detection, ``exploreValue`` aging.

        This populates the data structures every later phase reads.
        Direct port of ``Strategy.initTurn()`` (Strategy.java:78–202).
        """

        # ---- count close own-ant pairs (numCloseOwnAnts) -------------
        # Two of my ants are "close" if both row- and col-distance ≤ 5.
        # Used as an aggression signal in `_fight`. O(n²) over my ants;
        # xathis just iterates every pair.
        my_ants = self.my_ants
        for i, a in enumerate(my_ants):
            for b in my_ants[i + 1:]:
                if (self.dist_row(a.tile, b.tile) <= 5
                        and self.dist_col(a.tile, b.tile) <= 5):
                    a.num_close_own_ants += 1
                    b.num_close_own_ants += 1

        # ---- close-enemy distances + dangered/gamma flags -----------
        # For each (my_ant, enemy_ant) pair within CLOSE_ENEMY_RADIUS
        # rows AND cols, compute Euclidean² distance and populate the
        # ant-level lookup tables that drive safety / fight / escape.
        cer = CLOSE_ENEMY_RADIUS
        cer2 = CLOSE_ENEMY_RADIUS2
        for my_ant in self.my_ants:
            close: List[Tuple[int, Ant]] = []
            for enemy_ant in self.enemy_ants:
                dy = self.dist_row(my_ant.tile, enemy_ant.tile)
                if dy > cer:
                    continue
                dx = self.dist_col(my_ant.tile, enemy_ant.tile)
                if dx > cer:
                    continue
                d2 = dy * dy + dx * dx
                if d2 > cer2:
                    continue
                close.append((d2, enemy_ant))
                # mirror onto enemy
                enemy_ant.close_enemy_dists.append((d2, my_ant))
                my_ant.close_enemy_dists_sum += d2
                enemy_ant.close_enemy_dists_sum += d2
                # gamma: dr+dc ≤ 5, except the two corner cases (0,5)/(5,0)
                if (dx + dy <= 5
                        and not (dx == 0 and dy == 5)
                        and not (dy == 0 and dx == 5)):
                    if not my_ant.is_indirectly_dangered:
                        my_ant.is_indirectly_dangered = True
                    my_ant.gamma_dist_enemies.append(enemy_ant)
                    enemy_ant.gamma_dist_enemies.append(my_ant)
                    # dangered: dr+dc ≤ 4, except (0,4)/(4,0)
                    if (not my_ant.is_dangered
                            and dx + dy <= 4
                            and not (dx == 0 and dy == 4)
                            and not (dy == 0 and dx == 4)):
                        my_ant.is_dangered = True
                        self.dangered_ants.append(my_ant)
            if close:
                close.sort(key=lambda kv: kv[0])
                my_ant.close_enemy_dists = close
                my_ant.closest_enemy_tile = close[0][1].tile

        # Sort each enemy's close_enemy_dists too (xathis uses a TreeMap
        # so it's always sorted). We only need the head for combat.
        for enemy_ant in self.enemy_ants:
            if enemy_ant.close_enemy_dists:
                enemy_ant.close_enemy_dists.sort(key=lambda kv: kv[0])

        # ---- enemy-ant detached check + ordering --------------------
        # An enemy is "detached" if no other enemy is within (5,5) of it.
        # Used by attackDetachedEnemies. O(n²) again.
        for i, a in enumerate(self.enemy_ants):
            for b in self.enemy_ants[i + 1:]:
                if (self.dist_row(a.tile, b.tile) <= 5
                        and self.dist_col(a.tile, b.tile) <= 5):
                    a.is_detached = False
                    b.is_detached = False

        # ---- exploreValue aging + isBorder reset --------------------
        # Every tile's explore_value increments by 1 each turn; the
        # explore phase later resets it to 0 for tiles within reach.
        for row in self.tiles:
            for tile in row:
                tile.explore_value += 1
                tile.is_border = False
                if tile.ant is None:
                    tile.stay_value = -1

        # ---- willStay detection -------------------------------------
        # If an enemy ant has had the same neighborhood for ≥5 turns we
        # treat it as a permanent obstacle — saves combat search depth.
        for enemy in self.enemy_ants:
            curr_stay = 0
            for i, n in enumerate(enemy.tile.neighbors):
                if n.is_enemy():
                    curr_stay |= 1 << i
            tile = enemy.tile
            if tile.stay_value == curr_stay:
                tile.stay_turn_count += 1
                if tile.stay_turn_count >= 5:
                    enemy.will_stay = True
            else:
                tile.stay_value = curr_stay
                tile.stay_turn_count = 0
                enemy.will_stay = False

    def _calc_num_close_enemies(self) -> None:
        """BFS up to dist 12 from every enemy ant, populating each my-ant's
        ``num_close_enemies`` and ``closest_enemy``. Used by combat
        approach logic and ``escape``.

        Direct port of ``Strategy.calcNumCloseEnemies`` (Strategy.java:224).
        """
        for enemy in self.enemy_ants:
            if not enemy.close_enemy_dists:
                continue
            open_list: Deque[Tile] = deque()
            changed: List[Tile] = []
            enemy_tile = enemy.tile
            open_list.append(enemy_tile)
            enemy_tile.dist = 0
            enemy_tile.is_reached = True
            changed.append(enemy_tile)
            while open_list:
                t = open_list.popleft()
                if t.dist >= 12:
                    break
                for n in t.neighbors:
                    if n.is_reached:
                        continue
                    n.is_reached = True
                    n.dist = t.dist + 1
                    changed.append(n)
                    open_list.append(n)
                    if n.tile_type == MY_ANT and n.ant is not None:
                        n.ant.num_close_enemies += 1
                        if n.ant.closest_enemy_dist > n.dist:
                            n.ant.closest_enemy = enemy
                            n.ant.closest_enemy_dist = n.dist
            for t in changed:
                t.is_reached = False

    def _init_missions(self) -> None:
        """TODO: re-attach ongoing missions to current ants.
        Strategy.java:263-280."""
        pass

    def _enemy_hills(self) -> None:
        """Send up to ``count`` attackers per enemy hill via BFS outward.

        ``count`` = 1 if I have ≤10 ants, else 4 — small colonies can't
        spare more than one attacker, big colonies should mass-rush hills.

        Algorithm (Strategy.java:486-514):
        1. BFS from each enemy hill, depth ≤ 20.
        2. Each time the wave reaches a my-ant tile, send that ant one
           step toward the hill (i.e. to the tile we arrived at it from,
           which is the BFS predecessor).
        3. Skip if the ant has already moved, the predecessor is another
           my-ant, or the move is unsafe (``is_tile_safe`` gate).
        4. Decrement count for each my-ant reached (whether moved or not);
           stop when count ≤ 0.
        """
        if not self.enemy_hills:
            return
        count_per_hill = 1 if len(self.my_ants) <= 10 else 4
        for hill in self.enemy_hills:
            count = count_per_hill
            open_list: Deque[Tile] = deque()
            changed: List[Tile] = [hill]
            hill.dist = 0
            hill.is_reached = True
            open_list.append(hill)
            while open_list:
                t = open_list.popleft()
                if t.dist >= 20:
                    break
                for n in t.neighbors:
                    if n.is_reached:
                        continue
                    n.is_reached = True
                    if n.tile_type == MY_ANT and n.ant is not None:
                        ant = n.ant
                        # Try to send this ant one step closer to the hill
                        # (i.e. to the tile we expanded from). Skip if the
                        # predecessor is another my-ant, the ant already
                        # moved, or it's unsafe.
                        if (not ant.has_moved
                                and t.tile_type != MY_ANT
                                and self.is_tile_safe(ant, t)):
                            self.do_move(n, t, "enemy hill")
                        count -= 1
                    n.dist = t.dist + 1
                    changed.append(n)
                    open_list.append(n)
                if count <= 0:
                    break
            for tile in changed:
                tile.is_reached = False

    def _food(self) -> None:
        """Multi-source BFS from every food tile simultaneously. The first
        of my ants the wave reaches claims that food and moves toward it,
        gated by a suicide check (and a backup check if unsafe).

        Direct port of ``Strategy.food`` (Strategy.java:516–585) — the
        single biggest reason xathis was so efficient at growing his colony.
        """
        if not self.foods:
            return

        # ``source[tile]`` = which food this BFS branch came from.
        # ``enemy_near[food]`` flags food sources that have an enemy at
        # dist ≤ 2 — those get abandoned (don't fight to the death over
        # one piece of food).
        enemy_near: Dict[Tile, bool] = {}
        # Food sources we've already abandoned/claimed; tiles whose
        # ``source`` is in here get skipped on dequeue.
        dead_sources: Set[Tile] = set()

        open_list: Deque[Tile] = deque()
        changed: List[Tile] = []
        for food in self.foods:
            food.dist = 0
            food.is_reached = True
            food.source = food
            food.prev = None
            enemy_near[food] = False
            changed.append(food)
            open_list.append(food)

        while open_list:
            t = open_list.popleft()
            src = t.source
            if src is None or src in dead_sources:
                continue

            # Enemy-near-food early-warning: if the wave reaches an enemy
            # ant within dist 2 of the food, mark that food source as
            # contested.
            if t.dist <= 2 and t.is_enemy():
                enemy_near[src] = True

            # If we're past the contested zone and the food is contested,
            # abandon it entirely.
            if t.dist > 2 and enemy_near.get(src, False):
                dead_sources.add(src)
                continue

            # If the wave reached one of my ants, that ant claims the food.
            if (t.tile_type == MY_ANT and t.ant is not None and not t.ant.has_moved
                    and t.prev is not None
                    and t.prev.tile_type != MY_ANT):
                ant = t.ant
                # If the food is adjacent (prev is the food itself), just
                # stay put and let the ant pick it up next turn.
                if t.prev is src:
                    ant.has_moved = True
                elif not self.is_suicide(ant, t.prev):
                    enemy_block = self.is_tile_safe2(ant, t.prev)
                    if enemy_block is None:
                        # safe move; just go
                        self.do_move(t, t.prev, "food")
                    else:
                        # not safe — only proceed if we have backup
                        if self._food_has_backup(src, ant, enemy_block):
                            self.do_move(t, t.prev, "food")
                # food source consumed regardless of whether we managed
                # to actually move (avoids two ants chasing the same food).
                dead_sources.add(src)
                continue

            # Otherwise expand if still within food horizon.
            if t.dist < FOOD_BFS_HORIZON:
                next_dist = t.dist + 1
                for n in t.neighbors:
                    if n.is_reached:
                        continue
                    n.is_reached = True
                    n.prev = t
                    n.dist = next_dist
                    n.source = src
                    changed.append(n)
                    open_list.append(n)

        for t in changed:
            t.is_reached = False
            t.source = None

    def _food_has_backup(self, food: Tile, claimer: Ant, blocker: Ant) -> bool:
        """Return True if I have a my-ant near the food source that's
        *not* the claimer and *not* the blocking enemy.

        Mirrors the ``iHaveBackup`` block inside ``Strategy.food``
        (Strategy.java:548–560). The logic is "I can sacrifice the
        closer ant only if a follow-up ant is en route."
        """
        # Find the closest 3 ants (any owner) within dist 8 of the food.
        candidates: List[Tuple[int, Ant]] = []
        for ant in self.my_ants + self.enemy_ants:
            d = self.dist(food, ant.tile)
            if d < 8:
                candidates.append((d, ant))
                if len(candidates) >= 3:
                    break
        candidates.sort(key=lambda kv: kv[0])
        for _, ant in candidates:
            if ant is claimer or ant is blocker:
                continue
            return ant.tile.tile_type == MY_ANT
        return False

    def _init_explore(self) -> None:
        """Multi-source BFS from every my-ant; zero ``explore_value`` for
        every tile within 10 steps of any of my ants.

        Tiles outside that radius keep their per-turn-aged ``explore_value``
        (incremented in :meth:`_init_turn`), so they look "stale" to the
        :meth:`_explore` BFS and pull ants outward.

        Direct port of ``Strategy.initExplore`` (Strategy.java:891–916).
        """
        if not self.my_ants:
            return
        open_list: Deque[Tile] = deque()
        changed: List[Tile] = []
        for ant in self.my_ants:
            t = ant.tile
            if t.is_reached:
                continue
            t.dist = 0
            t.is_reached = True
            t.start_tile = t
            changed.append(t)
            open_list.append(t)
        # Java uses `if (tile.dist > 10) break` — process dist 0..10 inclusive.
        horizon = EXPLORE_BFS_HORIZON - 1  # = 10
        while open_list:
            t = open_list.popleft()
            if t.dist > horizon:
                break
            t.explore_value = 0
            for n in t.neighbors:
                if n.is_reached:
                    continue
                n.is_reached = True
                n.prev = t
                n.dist = t.dist + 1
                n.start_tile = t.start_tile
                changed.append(n)
                open_list.append(n)
        for t in changed:
            t.is_reached = False

    def _create_areas(self) -> None:
        """TODO: territory flood-fill + border tile detection.
        Strategy.java:678-771."""
        pass

    def _fight(self) -> None:
        """Group-based depth-1 minimax over gamma-distance combat groups.

        This is a *simplified* port of ``Strategy.fight`` (Strategy.java:781-874).
        xathis's full version uses dependency tables, alpha-beta cuts, and
        prec-grouping to handle large groups; we use exhaustive search
        capped at ``FIGHT_GROUP_CAP`` ants per side, which empirically
        handles 1v1, 1v2, 2v2, 3v2, 3v3 — the cases that matter most for
        breaking ties against scripted bots.

        For each gamma group (connected component via ``gamma_dist_enemies``):

        1. Enumerate every my-move combination (each my-ant: 4 neighbours
           + stay, with collision filtering).
        2. For each my-combo, find the *worst-case* enemy combo using the
           same enumeration.
        3. Score = my_kills − my_losses (computed via the actual AI
           Challenge battle-resolution rule).
        4. Pick the my-combo whose worst-case score is highest. Ties go
           to "stay" combos (more conservative).
        5. Apply the chosen moves; mark all ants in the group as moved.

        Bounded by ``TURN_TIME_BUDGET_MS`` (420ms) to avoid engine timeouts
        in heavy combat scenarios.
        """
        if not self.my_ants or not self.enemy_ants:
            return
        # Reset gamma_grouped flags (set by previous-turn iterations or
        # by an earlier loop on this turn).
        for a in self.my_ants:
            a.is_gamma_grouped = False
        for e in self.enemy_ants:
            e.is_gamma_grouped = False

        for start_ant in self.my_ants:
            if start_ant.has_moved or not start_ant.gamma_dist_enemies:
                continue
            if start_ant.is_gamma_grouped:
                continue
            # Time budget — bail if we're past 420ms.
            elapsed = time.monotonic() * 1000.0 - self.start_time_ms
            if elapsed > TURN_TIME_BUDGET_MS:
                self.is_timeout = True
                break

            my_group, enemy_group = self._find_gamma_group(start_ant)
            if len(my_group) > FIGHT_GROUP_CAP or len(enemy_group) > FIGHT_GROUP_CAP:
                continue
            if not enemy_group:
                continue
            self._fight_group(my_group, enemy_group)

    def _find_gamma_group(self, start_ant: Ant) -> Tuple[List[Ant], List[Ant]]:
        """BFS via ``gamma_dist_enemies`` edges to gather one connected
        component of mutually-threatening ants.

        Direct port of ``Strategy.findGammaGroup`` (Strategy.java:1022).
        Returns (my_group, enemy_group). The caller must reset
        ``is_gamma_grouped`` after the turn (or before re-using).
        """
        my_group: List[Ant] = [start_ant]
        enemy_group: List[Ant] = []
        start_ant.is_gamma_grouped = True
        my_q: Deque[Ant] = deque([start_ant])
        enemy_q: Deque[Ant] = deque()
        while my_q or enemy_q:
            if my_q:
                m = my_q.popleft()
                for e in m.gamma_dist_enemies:
                    if not e.is_gamma_grouped:
                        e.is_gamma_grouped = True
                        enemy_q.append(e)
                        enemy_group.append(e)
            if enemy_q:
                e = enemy_q.popleft()
                for m in e.gamma_dist_enemies:
                    if m.is_gamma_grouped or m.has_moved:
                        continue
                    m.is_gamma_grouped = True
                    my_q.append(m)
                    my_group.append(m)
        return my_group, enemy_group

    def _fight_options(self, ant: Ant, exclude_friendly_tiles: Set[Tile]) -> List[Tile]:
        """Return the list of destinations ``ant`` can attempt this turn.

        Always includes "stay" (its current tile). Adds each cardinal
        neighbour that is currently free of water, food, hills, and any
        ``exclude_friendly_tiles`` (other ants' current positions in the
        group — collision avoidance).

        For enemy ants we don't know about hills the same way; we just
        gate on ``is_free()`` (excludes water/food/ants).
        """
        opts: List[Tile] = [ant.tile]  # stay
        for n in ant.tile.neighbors:
            if n is ant.tile:
                continue
            if n.tile_type == WATER:
                continue
            if n.is_free() and n not in exclude_friendly_tiles:
                opts.append(n)
        return opts

    def _fight_group(self, my_group: List[Ant], enemy_group: List[Ant]) -> None:
        """Exhaustive minimax over all (my, enemy) move combinations,
        scored by the AI Challenge's mutual-destruction rule.
        """
        my_tiles = {a.tile for a in my_group}
        enemy_tiles = {e.tile for e in enemy_group}

        my_options: List[List[Tile]] = [
            self._fight_options(a, my_tiles - {a.tile}) for a in my_group
        ]
        enemy_options: List[List[Tile]] = [
            self._fight_options(e, enemy_tiles - {e.tile}) for e in enemy_group
        ]

        # Combination size sanity gate — even with cap=4 this can hit
        # 5^4 * 5^4 = ~390k combinations. Skip pathological branches.
        my_size = 1
        for opts in my_options:
            my_size *= len(opts)
        enemy_size = 1
        for opts in enemy_options:
            enemy_size *= len(opts)
        if my_size * enemy_size > FIGHT_BRANCHING_CAP:
            # Too expensive — fall through and let safety gates handle it.
            return

        best_score = -(1 << 30)
        best_combo: Optional[Tuple[Tile, ...]] = None

        for my_combo in self._iter_combos(my_options):
            # Quick collision check inside the my-side combo.
            if len(set(my_combo)) != len(my_combo):
                continue
            # Time check inside the inner loop too — combat search must
            # stay under budget.
            elapsed = time.monotonic() * 1000.0 - self.start_time_ms
            if elapsed > TURN_TIME_BUDGET_MS:
                self.is_timeout = True
                break
            worst_score = 1 << 30
            for enemy_combo in self._iter_combos(enemy_options):
                if len(set(enemy_combo)) != len(enemy_combo):
                    continue
                score = self._eval_battle(
                    my_group, my_combo, enemy_group, enemy_combo
                )
                if score < worst_score:
                    worst_score = score
                    if worst_score <= best_score:
                        # Alpha-prune: this my-combo can't beat the
                        # current best regardless of further enemy moves.
                        break
            if worst_score > best_score:
                best_score = worst_score
                best_combo = my_combo

        if best_combo is None:
            return

        # Apply best moves. Stays are noted as has_moved=True; real
        # moves go through do_move so the engine and tile graph stay in
        # sync.
        for ant, dest in zip(my_group, best_combo):
            if ant.has_moved:
                continue
            if dest is ant.tile:
                ant.has_moved = True
                continue
            self.do_move(ant.tile, dest, "fight")

    def _iter_combos(self, options: List[List[Tile]]):
        """Generator of every combination of one tile from each list.

        Plain Cartesian product, but we keep it as an explicit loop to
        allow alpha-pruning by the caller (the Python builtin
        ``itertools.product`` is fine but tuple-allocates eagerly).
        """
        n = len(options)
        if n == 0:
            yield ()
            return
        idx = [0] * n
        sizes = [len(o) for o in options]
        while True:
            yield tuple(options[i][idx[i]] for i in range(n))
            # increment
            i = 0
            while i < n:
                idx[i] += 1
                if idx[i] < sizes[i]:
                    break
                idx[i] = 0
                i += 1
            if i == n:
                return

    def _eval_battle(self, my_group: List[Ant], my_combo: Tuple[Tile, ...],
                     enemy_group: List[Ant], enemy_combo: Tuple[Tile, ...]) -> int:
        """Score = (enemy_dead − my_dead) under official AI Challenge
        battle resolution applied to the post-move positions.

        Rule (verbatim from the engine): each ant counts the opposing
        ants in its alpha-distance ("attackradius²") as its threat
        count. An ant dies if any opposing ant within attack range has
        a threat count ≤ its own. (1v1 → both die; 2v1 → the lone ant
        dies, both attackers survive.)

        We add small tie-breakers:
         * Penalize my-ants ending on hills (they block spawning).
         * Reward sitting *on* an enemy hill (razing wins games).
         * Add a tiny "ground covered" bonus to break stay/move ties so
           the bot doesn't freeze in place.
        """
        my_dead = 0
        enemy_dead = 0
        # Threat counts.
        my_threat = [0] * len(my_combo)
        enemy_threat = [0] * len(enemy_combo)
        for i, mt in enumerate(my_combo):
            for j, et in enumerate(enemy_combo):
                if self.is_alpha_dist(mt, et):
                    my_threat[i] += 1
                    enemy_threat[j] += 1
        # Death pass.
        for i, mt in enumerate(my_combo):
            if my_threat[i] == 0:
                continue
            for j, et in enumerate(enemy_combo):
                if not self.is_alpha_dist(mt, et):
                    continue
                if my_threat[i] >= enemy_threat[j]:
                    my_dead += 1
                    break
        for j, et in enumerate(enemy_combo):
            if enemy_threat[j] == 0:
                continue
            for i, mt in enumerate(my_combo):
                if not self.is_alpha_dist(mt, et):
                    continue
                if enemy_threat[j] >= my_threat[i]:
                    enemy_dead += 1
                    break

        score = (enemy_dead - my_dead) * 1000

        # Hill-based tie-breakers only. Movement bonus is intentionally
        # NOT applied here — fight is conservative; other phases handle
        # exploration/distribution. A move that results in mutual
        # destruction must score *exactly* 0 vs a stay that also scores
        # 0, so the deterministic "stay first" tie-break wins.
        for mt in my_combo:
            if mt.is_hill and mt.hill_player > 0:
                score += 50  # raze enemy hill is worth more than a trade
        return score

    def _defence(self) -> None:
        """Run :meth:`_defend_hill` for each of my hills, but skip if I
        have more than 4 hills (sprawled-too-thin signal).

        Direct port of ``Strategy.defence`` (Strategy.java:368-371).
        """
        if len(self.my_hills) > 4:
            return
        for hill in self.my_hills:
            self._defend_hill(hill)

    def _defend_hill(self, hill: Tile) -> None:
        """Find the closest enemy threatening this hill and send the
        nearest defender on the BFS path to intercept.

        Simplified port of ``Strategy.defendHill`` (Strategy.java:377-484).
        The original uses A* + a fallback BFS from the path's quarter
        point; we stick to a single hill-rooted BFS and grab the first
        my-ant on the enemy's prev chain. This is ~80% as effective and
        avoids needing A* until later phases.

        Algorithm:
        1. BFS from ``hill``, depth ≤ 14, also setting ``hill_dist`` on
           reached tiles. Collect every enemy ant tile encountered.
        2. Sort the threats by ``hill_dist`` (closest first).
        3. For each threat, walk back along the prev chain. If we hit a
           my-ant on the path, that ant is the defender — move it one
           step toward the enemy (the unique neighbour whose
           ``prev`` == defender's tile).
        4. ``is_suicide`` gate before issuing the move.
        """
        open_list: Deque[Tile] = deque()
        changed: List[Tile] = [hill]
        threats: List[Tile] = []
        hill.hill_dist = 0
        hill.is_reached = True
        hill.prev = None
        open_list.append(hill)
        while open_list:
            t = open_list.popleft()
            if t.hill_dist >= DEFENCE_HORIZON:
                break
            for n in t.neighbors:
                if n.is_reached:
                    continue
                n.is_reached = True
                n.hill_dist = t.hill_dist + 1
                n.prev = t
                # Strategy.java:394 — tiles within 10 of any hill count
                # as "known territory" for explore purposes.
                if n.hill_dist <= 10:
                    n.explore_value = 0
                changed.append(n)
                open_list.append(n)
                if n.is_enemy():
                    threats.append(n)

        # Sort enemies by hill_dist ascending (closest first), with a
        # stable secondary order on (row, col) to keep tests deterministic.
        threats.sort(key=lambda t: (t.hill_dist, t.row, t.col))

        for enemy_tile in threats:
            # Walk back along prev chain looking for a my-ant defender.
            t: Optional[Tile] = enemy_tile
            defender: Optional[Ant] = None
            step_after_defender: Optional[Tile] = None  # the step toward enemy
            while t is not None and not t.is_hill:
                if (t.tile_type == MY_ANT and t.ant is not None
                        and not t.ant.has_moved):
                    defender = t.ant
                    break
                step_after_defender = t
                t = t.prev

            if defender is None:
                # Fallback: also check the immediate cardinal neighbours
                # of the prev-chain. This catches a defender adjacent to
                # the path (xathis's logic at Strategy.java:434).
                t = enemy_tile
                while t is not None and not t.is_hill:
                    for n in t.neighbors:
                        if (n.tile_type == MY_ANT and n.ant is not None
                                and not n.ant.has_moved):
                            defender = n.ant
                            step_after_defender = t
                            break
                    if defender is not None:
                        break
                    t = t.prev

            if defender is None or step_after_defender is None:
                continue

            # The "step toward enemy" must be a direct neighbour of the
            # defender's current tile. If the prev-chain step isn't a
            # cardinal neighbour, skip rather than issue a bad move.
            if step_after_defender not in defender.tile.neighbors:
                continue
            if not step_after_defender.is_free():
                continue
            if self.is_suicide(defender, step_after_defender):
                continue
            self.do_move(defender.tile, step_after_defender, "defend")

        # Cleanup is_reached. hill_dist / prev are kept until next turn
        # (they get overwritten on the next BFS, no correctness issue).
        for tile in changed:
            tile.is_reached = False

    def _approach_enemies(self) -> None:
        """TODO: A* path toward closest enemy for fight-area ants.
        Strategy.java:876-889."""
        pass

    def _attack_detached_enemies(self) -> None:
        """TODO: pile on isolated enemy ants.
        Strategy.java:587-593."""
        pass

    def _escape_enemies(self) -> None:
        """TODO: dangered ants pick the safest neighbor via 8-step BFS.
        Strategy.java:595-666."""
        pass

    def _distribute(self, only_near_enemy: bool) -> None:
        """TODO: spread out by maximizing reachable-tile count.
        Strategy.java:990-1014."""
        pass

    def _explore(self) -> None:
        """For each idle, non-indirectly-dangered ant, run :meth:`_explore_ant`
        which picks the cardinal step that pulls in the most "fog" value
        from the 10-step horizon.

        Direct port of ``Strategy.explore`` (Strategy.java:917–922).
        """
        for ant in self.my_ants:
            if ant.has_moved or ant.is_indirectly_dangered:
                continue
            self._explore_ant(ant)

    def _explore_ant(self, ant: Ant) -> bool:
        """Diffusion-style frontier scoring around a single ant.

        Algorithm (Strategy.java:923–988):

        1. BFS from the ant's tile, depth ≤ 10.
        2. The 4 cardinal neighbours are the candidate "first steps". For
           each tile reached on a *shortest* path, record which first
           steps lead to it (``prev_firsts`` — multiple ties accumulate).
        3. When a tile is dequeued at the horizon (dist > 10), do **not**
           expand it. Instead distribute its accumulated ``explore_value``
           equally to every first step that owns a shortest path to it.
        4. The first step with the highest summed value wins. Ties go to
           whichever entry was inserted first (i.e. dict order — that's
           the cardinal order ``n``/``e``/``s``/``w``).
        5. The destination must be ``is_free()`` AND not a hill (avoid
           overwriting food/ant tiles or stalling on a friendly hill).
        6. After picking the destination, zero out the ``explore_value``
           of every frontier tile that the chosen first step "owns", so
           subsequent ants pursue different frontiers.

        Returns True if a move was issued, False otherwise (caller may
        fall through to other phases — ``_distribute`` etc.).
        """
        ant_tile = ant.tile
        # values[first_step_tile] = cumulative explore_value from frontier.
        # Insertion order matters because we tie-break by it.
        values: Dict[Tile, int] = {}
        open_list: Deque[Tile] = deque()
        changed: List[Tile] = [ant_tile]
        ant_tile.is_reached = True
        ant_tile.dist = 0

        for n in ant_tile.neighbors:
            values[n] = 0
            n.dist = 1
            n.is_reached = True
            n.prev_firsts.add(n)
            changed.append(n)
            open_list.append(n)

        horizon = EXPLORE_BFS_HORIZON - 1  # = 10
        while open_list:
            t = open_list.popleft()
            if t.dist > horizon:
                # Frontier tile: distribute its exploreValue to each
                # first-step that has a shortest path to it.
                ev = t.explore_value
                if ev:
                    for first in t.prev_firsts:
                        if first in values:
                            values[first] += ev
                continue
            for n in t.neighbors:
                if n.is_reached:
                    # Equal-distance tie: this neighbour was reached via
                    # a different first-step on the same depth, so unify
                    # the prev_firsts sets.
                    if n.dist == t.dist + 1:
                        n.prev_firsts.update(t.prev_firsts)
                    continue
                n.is_reached = True
                n.prev = t
                n.dist = t.dist + 1
                n.prev_firsts.update(t.prev_firsts)
                changed.append(n)
                open_list.append(n)

        # Pick the best free, non-hill first step.
        best_value = 0
        best_dest: Optional[Tile] = None
        for tile, v in values.items():
            if v > best_value and tile.is_free() and not tile.is_hill:
                best_value = v
                best_dest = tile

        if best_dest is None or best_value == 0:
            for t in changed:
                t.is_reached = False
                t.prev_firsts.clear()
            return False

        # Zero out frontier explore_values that the chosen first-step owns,
        # so other ants don't all swarm the same fog blob.
        for t in changed:
            if t.dist > horizon and best_dest in t.prev_firsts:
                t.explore_value = 0
            t.is_reached = False
            t.prev_firsts.clear()

        # Final safety gate: don't walk into death. The Java doesn't gate
        # explore (it relies on `isIndirectlyDangered` excluding ants in
        # combat range), but a belt-and-braces check costs nothing.
        if self.is_suicide(ant, best_dest):
            return False
        self.do_move(ant_tile, best_dest, "explore")
        return True

    def _do_missions(self) -> None:
        """TODO: A* each mission ant toward its target tile.
        Strategy.java:281-304."""
        pass

    def _create_missions(self) -> None:
        """TODO: assign new missions to idle ants in fight areas.
        Strategy.java:313-336."""
        pass

    def _clean_areas(self) -> None:
        """TODO: reset is_in_my_area flags for next turn.
        Strategy.java:773-777."""
        pass

    # ------------------------------------------------------------------
    # Safety gates (Strategy.java:1673-1724)
    # ------------------------------------------------------------------
    def is_tile_safe(self, ant: Ant, dest: Tile) -> bool:
        """True if moving ``ant`` to ``dest`` *cannot* result in attack
        next turn from any enemy in ``ant.gamma_dist_enemies``.

        For ``willStay`` enemies: only check their current position.
        For mobile enemies: dest must not be in beta of the enemy's
        current position; if the enemy has all 4 free neighbors, dest
        being in beta is automatic death; otherwise check each neighbor.

        Direct port of ``Strategy.isTileSafe`` (Strategy.java:1673).
        """
        for enemy in ant.gamma_dist_enemies:
            if enemy.will_stay:
                if self.is_alpha_dist(enemy.tile, dest):
                    return False
                continue
            if not self.is_beta_dist(enemy.tile, dest):
                continue
            if len(enemy.tile.neighbors) == 4:
                return False
            for n in enemy.tile.neighbors:
                if self.is_alpha_dist(n, dest):
                    return False
        return True

    def is_tile_safe2(self, ant: Ant, dest: Tile) -> Optional[Ant]:
        """Like :meth:`is_tile_safe`, but returns the *first* enemy that
        makes the destination unsafe (or None if safe). Used by
        :meth:`_food` to decide whether backup support is warranted.

        Direct port of ``Strategy.isTileSafe2`` (Strategy.java:1688).
        """
        for enemy in ant.gamma_dist_enemies:
            if enemy.will_stay:
                if self.is_alpha_dist(enemy.tile, dest):
                    return enemy
                continue
            if not self.is_beta_dist(enemy.tile, dest):
                continue
            if len(enemy.tile.neighbors) == 4:
                return enemy
            for n in enemy.tile.neighbors:
                if self.is_alpha_dist(n, dest):
                    return enemy
        return None

    def is_suicide(self, ant: Ant, dest: Tile) -> bool:
        """Stronger check than :meth:`is_tile_safe`: a move is suicide
        only if *two or more* enemies threaten the destination
        simultaneously (a 1-on-1 trade isn't necessarily a loss — it's
        a wash if our ant is supported).

        Direct port of ``Strategy.isSuicide`` (Strategy.java:1702).
        """
        dangered = False
        for enemy in ant.gamma_dist_enemies:
            if enemy.will_stay:
                if self.is_alpha_dist(enemy.tile, dest):
                    if dangered:
                        return True
                    dangered = True
                continue
            if not self.is_beta_dist(enemy.tile, dest):
                continue
            if len(enemy.tile.neighbors) == 4:
                if dangered:
                    return True
                dangered = True
            else:
                for n in enemy.tile.neighbors:
                    if self.is_alpha_dist(n, dest):
                        if dangered:
                            return True
                        dangered = True
                        break
        return False

    # ------------------------------------------------------------------
    # Move issuing
    # ------------------------------------------------------------------
    def do_move(self, src: Tile, dest: Tile, info: str = "") -> bool:
        """Issue a move from ``src`` to ``dest`` (must be a direct neighbor).

        Mirrors ``Strategy.doMove`` (Strategy.java:1656). Returns True if
        the move was issued. Does not perform safety checks — those are
        the caller's responsibility (most phase methods gate via
        ``is_tile_safe``).
        """
        if src.ant is None:
            return False
        if dest is src:
            src.ant.has_moved = True
            return True
        direction = src.dir_to(dest)
        # Update the tile graph.
        dest.tile_type = src.tile_type
        dest.ant = src.ant
        src.tile_type = LAND
        src.ant.tile = dest
        src.ant.has_moved = True
        src.ant = None
        # Tell the engine.
        self._engine.issue_order((src.row, src.col, direction))
        return True


def main() -> None:
    try:
        Ants.run(XathisBot())
    except KeyboardInterrupt:
        print("ctrl-c, leaving ...")


if __name__ == "__main__":
    main()
