"""Influence-map bot for Google's Ants AI Challenge.

Original strategy written by Tim Whitson and recovered from repository commit
``fd85c05``. The current project adapts its runtime seam and preserves it as an
attributed algorithmic baseline; it is not represented as original Taylor code.

Influence
---------

This bot uses an influence/heat map. Each item of interest (food, hill, etc.)
creates influence, which propagates over the map. Some tiles will have
negative influence, such as impassable tiles and tiles with large
enemy influence.

Rather than having each ant route tracing, the ants simply move into
the tile with the largest influence.


Exploration
-----------

Food tiles have large influence. They only affect one ant, however. This
hopefully creates emergent behavior so the ants spread out to find food.

Tiles within the edges of visibility for each ant are also tracked. If they
have not been seen within 5 turns, they also influence the ant to continue
moving forward.


Combat
------

This bot's combat is not sophisticated. It looks for enemy/ally influence
and tries to avoid any particularly bad situation. It also will sometimes
capitalize on enemy weaknesses.


Waves
-----

Once enough ants are present, a large influencer (wave) is generated that
moves toward the enemy spawn. The idea is to collect the ants and move them
in a cohesive unit toward the enemy hill. Momentum is also important as
ants in motion are less likely to be killed and can explore/pick up food.
"""

from math import sqrt

from ants import FOOD, WATER, Ants  # pylint: disable=no-name-in-module

# custom
MY_HILL = 10
ALLY_ANT = 20
ENEMY_HILL = 30
ENEMY_ANT = 40
WAVE = 50
NOT_VISIBLE = 60

# how strongly each item influence ants
influence_values = {FOOD: 20, ENEMY_HILL: 50, WAVE: 5, NOT_VISIBLE: 0.1}

# total number of ants each individual item can influence
number_of_influences = {FOOD: 1, WAVE: 2, NOT_VISIBLE: 1, MY_HILL: 4}

stop_propagation = [WATER]
stop_locs = set()

blocked = [FOOD, WATER]

nrows = 0  # pylint: disable=invalid-name
ncols = 0  # pylint: disable=invalid-name


def wrap_loc(loc):
    """Wrap location around map"""
    r, c = loc
    return (r % nrows, c % ncols)


class Wave:  # pylint: disable=too-few-public-methods
    """Line of influence, that moves N/S depending on start location
    bringing a wave of ants
    """

    def __init__(self, left, width=4):
        locs = [left]
        for i in range(1, width + 1):
            locs.append((left[0], left[1] + i))

        self.locs = locs

    def move(self, direction):
        """Move every location in the wave one tile in ``direction``."""
        move = {"n": (-1, 0), "s": (1, 0), "e": (0, 1), "w": (0, -1)}[direction]

        self.locs = [wrap_loc((l[0] + move[0], l[1] + move[1])) for l in self.locs]


class IForOneWelcomeOurNewInsectOverlords:  # pylint: disable=too-many-instance-attributes
    """Historical influence-map strategy with a current-protocol adapter."""

    def __init__(self):
        # Store hill locations since they do not move on this map.
        self.my_hill = None
        self.enemy_hill = None
        self.waves = []
        self.wave_dir = None
        self.view_distance = 0.0
        self.visibility_map = []
        self._vision_offsets = ()
        self._visible_locs = set()
        self._is_setup = False

    def do_setup(self, ants):
        """Set initial variables"""
        self.view_distance = sqrt(ants.viewradius2)
        self.visibility_map = self.map_zeros(ants.map)
        vision_radius = int(self.view_distance)
        self._vision_offsets = tuple(
            (row_delta, col_delta)
            for row_delta in range(-vision_radius, vision_radius + 1)
            for col_delta in range(-vision_radius, vision_radius + 1)
            if row_delta**2 + col_delta**2 <= ants.viewradius2
        )

        global nrows, ncols  # pylint: disable=global-statement
        nrows = len(self.visibility_map)
        ncols = len(self.visibility_map[0])
        stop_locs.clear()
        self._is_setup = True

    @staticmethod
    def _distance(ants, first, second):
        """Bridge the historical tuple API to the current bot helper."""
        return ants.distance(first[0], first[1], second[0], second[1])

    @staticmethod
    def _destination(ants, loc, direction):
        """Bridge the historical tuple API to the current bot helper."""
        return ants.destination(loc[0], loc[1], direction)

    def _visible(self, loc):
        """Return whether ``loc`` is inside any friendly ant's vision circle."""
        return loc is not None and loc in self._visible_locs

    def map_zeros(self, amap):
        """Create map of zeroes the same size as given"""
        zm = [0] * len(amap)

        for i in range(len(amap)):
            zm[i] = [0] * len(amap[0])

        return zm

    def update_visibility(self, my_ants):
        """Update locations that have been seen as 0,
        increment locations that are not visible (number of turns that loc was not visible)
        """
        for row in self.visibility_map:
            for col, value in enumerate(row):
                row[col] = value + 1

        height = len(self.visibility_map)
        width = len(self.visibility_map[0])
        self._visible_locs = {
            (
                (ant_row + row_delta) % height,
                (ant_col + col_delta) % width,
            )
            for ant_row, ant_col in my_ants
            for row_delta, col_delta in self._vision_offsets
        }
        for row, col in self._visible_locs:
            self.visibility_map[row][col] = 0

    def set_stop_locs(self, amap):
        """Locations that stop propagation of the BFS
        ie. water
        """
        for r, row in enumerate(amap):
            for c, col in enumerate(row):
                if col in stop_propagation:
                    stop_locs.add((r, c))

    def influence_locs(self, amap):
        """Iterate over map, if tile value (hills, food, etc)
        has influence value, add to list
        """
        locs = []

        for r, row in enumerate(amap):
            for c, col in enumerate(row):
                if col in influence_values:
                    locs.append(((r, c), influence_values[col]))

        return locs

    def add_to_map(self, amap, locs, value):
        """Add custom values to ants map

        ie. to differentiate between ally and enemy ants
        """
        for r, c in locs:
            amap[r][c] = value

        return amap

    def map_influence(self, amap, locs, my_ants):
        """Breadth-first search to create influence map. A starting point is
        given and each subsequent move (1-tile away) is stored as a list. The
        index of each list in the list of lists is its distance.

                            3
                          3 2 3
                        3 2 1 2 3
                          3 2 3
                            3

        If maximum number of ants is reached, stop propagation.
        """

        def build_influence(start_loc):
            influence_locs = [[start_loc]]
            queue = [start_loc]
            old_locs = {start_loc}  # use set for improved performance
            num_ants = 0
            max_ants = number_of_influences.get(
                amap[start_loc[0]][start_loc[1]], len(my_ants)
            )

            while True:
                new_locs = []

                for loc in queue:
                    for direction in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        add = (loc[0] + direction[0], loc[1] + direction[1])
                        add = wrap_loc(add)

                        stop = add in stop_locs

                        if add in my_ants:
                            num_ants += 1

                            if num_ants >= max_ants:
                                influence_locs.append(new_locs)
                                return influence_locs

                        if add not in old_locs and not stop:
                            old_locs.add(add)
                            new_locs.append(add)

                queue = new_locs

                if not queue:
                    return influence_locs

                influence_locs.append(new_locs)

            return influence_locs

        influences = [(build_influence(loc), strength) for loc, strength in locs]
        return influences

    def add_influence(self, imap, influences):
        """Add influence values to blank map (map of zeros)"""
        for influence, strength in influences:
            for dist, locs in enumerate(influence):
                for loc in locs:
                    r, c = loc
                    val = strength / (dist + 1)
                    imap[r][c] += val

        return imap

    def locs_within(self, loc, distance, true_distance=False):
        """Get all locations within distance from loc"""
        locs = []
        for r in range(loc[0] - distance, loc[0] + distance + 1):
            for c in range(loc[1] - distance, loc[1] + distance + 1):
                compare = distance + 1 if true_distance else distance
                if abs(loc[0] - r) + abs(loc[1] - c) <= compare:
                    locs.append(wrap_loc((r, c)))

        return locs

    def edge_locs(self, locs, _ants):
        """Retrieve the edges of visibility for each ant"""
        distance = int(self.view_distance) + 1
        edges = set()

        for loc in locs:
            for r in range(loc[0] - distance, loc[0] + distance + 1):
                for c in range(loc[1] - distance, loc[1] + distance + 1):
                    if abs(loc[0] - r) + abs(loc[1] - c) == distance:
                        edge_loc = wrap_loc((r, c))
                        if self.visibility_map[edge_loc[0]][edge_loc[1]] >= 5:
                            edges.add(edge_loc)

        return edges

    def combat_map(  # pylint: disable=too-many-locals
        self, mmap, my_ants, enemy_ants, ants
    ):
        """Set locs on map related to combat

        These locs work differently from the rest. They do not propagate.
        The idea is to set low (unmoveable) values on tiles where an ant
        is sure to be killed.
        """
        kill_radius = 2
        die_locs = []

        # enemies influence each possible square they could attack the next turn
        for loc in enemy_ants:
            move_locs = self.locs_within(loc, 1)
            enemy_moves = set()
            for move_loc in move_locs:
                enemy_moves.update(
                    self.locs_within(move_loc, kill_radius, true_distance=True)
                )

            die_locs.extend(enemy_moves)

        for r, c in die_locs:
            mmap[r][c] -= 150

        # Use only ants within move + attack + enemy move distance
        # (1 + 2 + 1 = 4) of an enemy.
        my_eligible_ants = [
            ant
            for ant in my_ants
            if any(
                self._distance(ants, ant, enemy) <= kill_radius + 2
                for enemy in enemy_ants
            )
        ]

        attack_locs = []

        # influence only one tile away, unless touching another ant
        for loc in my_eligible_ants:
            ants_touching = any(
                self._distance(ants, loc, ant) == 1 for ant in my_eligible_ants
            )
            ally_moves = self.locs_within(loc, 1, true_distance=ants_touching)
            attack_locs.extend(ally_moves)

        for loc in attack_locs:
            if loc in die_locs:
                r, c = loc
                mmap[r][c] += 100

        return mmap

    def hill_defense(self, enemy_ants, ants, standoff=7):
        """Determine whether or not hill needs defending"""
        if self.my_hill is None:
            return []
        if not self._visible(self.my_hill) or any(
            self._distance(ants, enemy, self.my_hill) <= standoff
            for enemy in enemy_ants
        ):
            return [(self.my_hill, 50)]
        return []

    def issue_orders(self, my_ants, ants, mmap):
        """Loop through queue of ants, removing them if they have a valid space to move into."""
        prev_destinations = set()

        level = 0
        turns_without_order = 0

        while my_ants:
            loc = my_ants.pop(0)

            # look for marker in queue, if so the following ants will choose their next best spot
            # also check if too many turns have passed without issuing an order (this typically
            # happens if ants want to move into each other's space)
            if loc is None or turns_without_order >= len(my_ants) + 1:
                level += 1
                if level > 4:
                    break
                continue

            # add current loc to possible directions
            directions = ["n", "s", "e", "w"]
            surrounding = [self._destination(ants, loc, d) for d in directions] + [loc]
            directions += ["stay"]

            # sort by best score
            influences = [mmap[r][c] for r, c in surrounding]
            max_idx = [
                i
                for _, i in sorted(
                    zip(influences, range(len(influences))), reverse=True
                )
            ][level]
            destination = directions[max_idx]

            # highest influence is current spot
            if destination == "stay":
                prev_destinations.add(loc)
                continue

            move_loc = surrounding[max_idx]

            # if moving into a square where another ant currently is, move to back of queue
            if move_loc in my_ants:
                my_ants.append(loc)
                turns_without_order += 1
                continue

            # trying to move into a space another ant has already chosen, append marker to queue
            if move_loc in prev_destinations:
                if None not in my_ants:
                    my_ants.append(None)
                my_ants.append(loc)
                continue

            # go!
            prev_destinations.add(move_loc)
            turns_without_order = 0
            ants.issue_order((loc[0], loc[1], destination))

    def do_turn(self, ants):  # pylint: disable=too-many-branches
        """Baked in turn function"""
        if not self._is_setup:
            self.do_setup(ants)
        my_ants = ants.my_ants()
        self.update_visibility(my_ants)

        # The historical code annotated the runtime map in place. Work on a
        # copy so strategy-only markers cannot leak into the protocol state.
        amap = [row[:] for row in ants.map]

        # add hills if not already added
        if not self.my_hill:
            self.my_hill = ants.my_hills()[0]

            if self.my_hill[0] > 21:
                self.wave_dir = "n"
            else:
                self.wave_dir = "s"

        if not self.enemy_hill and ants.enemy_hills():
            self.enemy_hill = ants.enemy_hills()[0][0]

        enemy_ants = [a[0] for a in ants.enemy_ants()]

        # add/remove waves if there are enough ants
        if len(my_ants) >= 10:
            if not self.waves:
                self.waves.append(Wave((0, 5), 11))
                self.waves.append(Wave((0, 23), 11))
        else:
            self.waves = []

        # influence map (zeros)
        imap = self.map_zeros(amap)

        # create spots which stop propagation, such as water
        self.set_stop_locs(amap)

        # add custom locs to map for influencing
        amap = self.add_to_map(amap, my_ants, ALLY_ANT)
        if self.my_hill:
            amap = self.add_to_map(amap, [self.my_hill], MY_HILL)

        amap = self.add_to_map(amap, enemy_ants, ENEMY_ANT)
        if self.enemy_hill:
            amap = self.add_to_map(amap, [self.enemy_hill], ENEMY_HILL)

        # get influence locations from ants map
        ilocs = self.influence_locs(amap)

        # waves
        for wave in self.waves:
            wave.move(self.wave_dir)
            for loc in wave.locs:
                ilocs.append((loc, influence_values[WAVE]))

        # add vision/edge influencers
        ilocs += [(loc, NOT_VISIBLE) for loc in self.edge_locs(my_ants, ants)]

        # check if hill needs defending
        ilocs += self.hill_defense(enemy_ants, ants)

        # influence list of lists
        influence = self.map_influence(amap, ilocs, my_ants)

        # add all influencers to map of zeros
        mmap = self.add_influence(imap, influence)

        # prevent ants from moving to where they will die
        mmap = self.combat_map(mmap, my_ants, enemy_ants, ants)

        # food/water tiles are blocking, so prevent movement to them
        for r, row in enumerate(amap):
            for c, tile in enumerate(row):
                if tile in blocked:
                    mmap[r][c] = -10000

        self.issue_orders(my_ants, ants, mmap)


# Short, descriptive name for docs, tests, and benchmark output while retaining
# the historical class name as the source identity.
InfluenceBot = IForOneWelcomeOurNewInsectOverlords


if __name__ == "__main__":
    try:
        Ants.run(InfluenceBot())  # pylint: disable=no-member
    except KeyboardInterrupt:
        print("ctrl-c, leaving ...")
