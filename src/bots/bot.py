#!/usr/bin/env python
from ants import *

# ============================================================================
# LEARNED WINNING BOT - Based on LeftyBot + GreedyBot insights
# ============================================================================

class AdvancedBot:
    """
    More Aggressive WINNING BOT - Designed to BEAT LeftyBot
    
    Key insights from studying LeftyBot:
    - LeftyBot's strength: Systematic exploration with wall-following
    - LeftyBot's weakness: No direct food hunting, relies on exploration luck
    - Our advantage: We can be MORE aggressive about food collection AND exploration
    
    Strategy to beat LeftyBot:
    1. More Aggressive food hunting (closer distances, more ants)
    2. More Aggressive multiplication (return to hill more frequently)
    3. Better exploration than LeftyBot (multiple exploration patterns)
    4. Strategic combat (hunt enemy ants when we have advantage)
    """
    
    def __init__(self):
        self.ants_straight = {}  # Ants moving in straight lines (from LeftyBot)
        self.ants_lefty = {}     # Ants following walls (from LeftyBot)
        self.standing_orders = []  # Continue tasks across turns (from GreedyBot)
        self.turn_count = 0
        
    def get_initial_direction(self, a_row, a_col):
        """Get initial direction for new ants based on position (from LeftyBot)"""
        if a_row % 2 == 0:
            if a_col % 2 == 0:
                return 'n'
            else:
                return 's'
        else:
            if a_col % 2 == 0:
                return 'e'
            else:
                return 'w'
    
    def do_turn(self, ants):
        """Combined LeftyBot exploration + GreedyBot priority system"""
        self.turn_count += 1
        destinations = []
        new_straight = {}
        new_lefty = {}
        orders = []
        hunted = []
        
        # Continue standing orders from previous turn (from GreedyBot)
        for order in self.standing_orders:
            ant_loc, step_loc, dest_loc, order_type = order
            if ((order_type == HILL and dest_loc in ants.enemy_hills()) or
                    (order_type == FOOD and dest_loc in ants.food()) or
                    (order_type == ANTS and dest_loc in ants.enemy_ants()) or
                    (order_type == UNSEEN and ants.map[dest_loc[0]][dest_loc[1]] == UNSEEN)):
                self.do_order(ants, order_type, ant_loc, dest_loc, destinations, hunted, orders)
        
        origins = [order[0] for order in orders]
        
        # More Aggressive priority system to beat LeftyBot
        for a_row, a_col in ants.my_ants():
            if (a_row, a_col) not in origins:
                # PRIORITY 1: Return to hill for multiplication (More Aggressive)
                if self.return_to_hill(ants, a_row, a_col, destinations, hunted, orders):
                    continue
                
                # PRIORITY 2: Hunt enemy hills (strategic)
                if self.hunt_hills(ants, a_row, a_col, destinations, hunted, orders):
                    continue
                
                # PRIORITY 3: Hunt food (More Aggressive)
                if self.hunt_food(ants, a_row, a_col, destinations, hunted, orders):
                    continue
                
                # PRIORITY 4: Hunt enemy ants (strategic combat)
                if self.hunt_ants(ants, a_row, a_col, destinations, hunted, orders):
                    continue
                
                # PRIORITY 5: Hunt unseen areas (exploration)
                if self.hunt_unseen(ants, a_row, a_col, destinations, hunted, orders):
                    continue
                
                # PRIORITY 6: Use LeftyBot's exploration strategy (but better)
                self.wall_following_strategy(ants, a_row, a_col, destinations, new_straight, new_lefty)
        
        # Update tracking dictionaries (from LeftyBot)
        self.ants_straight = new_straight
        self.ants_lefty = new_lefty
        self.standing_orders = orders
        
        # Update standing orders for next turn (from GreedyBot)
        for order in self.standing_orders:
            order[0] = order[1]
    
    def hunt_hills(self, ants, a_row, a_col, destinations, hunted, orders):
        """Find and move toward closest enemy hill"""
        closest_enemy_hill = ants.closest_enemy_hill(a_row, a_col)
        if closest_enemy_hill is not None:
            return self.do_order(ants, HILL, (a_row, a_col), closest_enemy_hill, destinations, hunted, orders)
        return False
    
    def hunt_food(self, ants, a_row, a_col, destinations, hunted, orders):
        """More Aggressive food hunting to beat LeftyBot"""
        closest_food = ants.closest_food(a_row, a_col, hunted)
        if closest_food is not None:
            # More Aggressive: Hunt food from much further away than LeftyBot
            distance = ants.distance(a_row, a_col, closest_food[0], closest_food[1])
            my_ants = ants.my_ants()
            total_ants = len(my_ants)
            
            # Be more aggressive when we have fewer ants (critical for beating LeftyBot)
            if total_ants <= 5:
                max_distance = 50  # Very aggressive when we need to catch up
            elif total_ants <= 10:
                max_distance = 40  # Still very aggressive
            elif total_ants <= 20:
                max_distance = 35  # Aggressive
            else:
                max_distance = 30  # Still aggressive even with many ants
            
            if distance <= max_distance:
                return self.do_order(ants, FOOD, (a_row, a_col), closest_food, destinations, hunted, orders)
        return False
    
    def hunt_ants(self, ants, a_row, a_col, destinations, hunted, orders):
        """More Aggressive enemy ant hunting to beat LeftyBot"""
        closest_enemy_ant = ants.closest_enemy_ant(a_row, a_col, hunted)
        if closest_enemy_ant is not None:
            # Only hunt enemy ants if we have more ants than them (strategic advantage)
            my_ants = ants.my_ants()
            enemy_ants = ants.enemy_ants()
            if len(my_ants) > len(enemy_ants):
                distance = ants.distance(a_row, a_col, closest_enemy_ant[0], closest_enemy_ant[1])
                # Hunt enemy ants from far away when we have advantage
                if distance <= 25:
                    return self.do_order(ants, ANTS, (a_row, a_col), closest_enemy_ant, destinations, hunted, orders)
        return False
    
    def return_to_hill(self, ants, a_row, a_col, destinations, hunted, orders):
        """More Aggressive hill return for maximum multiplication"""
        my_hills = ants.my_hills()
        if not my_hills:
            return False
        
        # Find closest hill
        closest_hill = min(my_hills, key=lambda hill: ants.distance(a_row, a_col, hill[0], hill[1]))
        distance_to_hill = ants.distance(a_row, a_col, closest_hill[0], closest_hill[1])
        
        my_ants = ants.my_ants()
        total_ants = len(my_ants)
        enemy_ants = ants.enemy_ants()
        enemy_count = len(enemy_ants)
        
        # More Aggressive multiplication strategy to beat LeftyBot
        if total_ants <= 20:  # Very aggressive when we have few ants
            return self.do_order(ants, HILL, (a_row, a_col), closest_hill, destinations, hunted, orders)
        
        # Return to hill if we're losing the ant race
        if enemy_count > total_ants:
            return self.do_order(ants, HILL, (a_row, a_col), closest_hill, destinations, hunted, orders)
        
        # Return to hill if we're close enough
        if distance_to_hill <= 15:  # Very aggressive distance
            return self.do_order(ants, HILL, (a_row, a_col), closest_hill, destinations, hunted, orders)
        
        return False
    
    def hunt_unseen(self, ants, a_row, a_col, destinations, hunted, orders):
        """Find and move toward closest unseen area"""
        closest_unseen = ants.closest_unseen(a_row, a_col, hunted)
        if closest_unseen is not None:
            return self.do_order(ants, UNSEEN, (a_row, a_col), closest_unseen, destinations, hunted, orders)
        return False
    
    def do_order(self, ants, order_type, loc, dest, destinations, hunted, orders):
        """Execute an order (from GreedyBot)"""
        a_row, a_col = loc
        directions = ants.direction(a_row, a_col, dest[0], dest[1])
        
        for direction in directions:
            (n_row, n_col) = ants.destination(a_row, a_col, direction)
            if (not (n_row, n_col) in destinations and
                ants.unoccupied(n_row, n_col)):
                ants.issue_order((a_row, a_col, direction))
                destinations.append((n_row, n_col))
                hunted.append(dest)
                orders.append([loc, (n_row, n_col), dest, order_type])
                return True
        return False
    
    def wall_following_strategy(self, ants, a_row, a_col, destinations, new_straight, new_lefty):
        """IMPROVED wall-following exploration strategy to beat LeftyBot"""
        # Send new ants in a straight line
        if (not (a_row, a_col) in self.ants_straight and
                not (a_row, a_col) in self.ants_lefty):
            direction = self.get_initial_direction(a_row, a_col)
            new_straight[(a_row, a_col)] = direction

        # Send ants going in a straight line in the same direction
        if (a_row, a_col) in self.ants_straight:
            direction = self.ants_straight[(a_row, a_col)]
            n_row, n_col = ants.destination(a_row, a_col, direction)
            if ants.passable(n_row, n_col):
                if (ants.unoccupied(n_row, n_col) and
                        not (n_row, n_col) in destinations):
                    ants.issue_order((a_row, a_col, direction))
                    new_straight[(n_row, n_col)] = direction
                    destinations.append((n_row, n_col))
                else:
                    # IMPROVEMENT: Try alternative directions instead of just turning
                    for alt_dir in [LEFT[direction], RIGHT[direction]]:
                        alt_row, alt_col = ants.destination(a_row, a_col, alt_dir)
                        if (ants.passable(alt_row, alt_col) and
                                ants.unoccupied(alt_row, alt_col) and
                                not (alt_row, alt_col) in destinations):
                            ants.issue_order((a_row, a_col, alt_dir))
                            new_straight[(alt_row, alt_col)] = alt_dir
                            destinations.append((alt_row, alt_col))
                            break
                    else:
                        # pause ant, turn and try again next turn
                        new_straight[(a_row, a_col)] = LEFT[direction]
                        destinations.append((a_row, a_col))
            else:
                # hit a wall, start following it
                new_lefty[(a_row, a_col)] = RIGHT[direction]

        # Send ants following a wall, keeping it on their left
        if (a_row, a_col) in self.ants_lefty:
            direction = self.ants_lefty[(a_row, a_col)]
            directions = [LEFT[direction], direction, RIGHT[direction], BEHIND[direction]]
            # try 4 directions in order, attempting to turn left at corners
            for new_direction in directions:
                n_row, n_col = ants.destination(a_row, a_col, new_direction)
                if ants.passable(n_row, n_col):
                    if (ants.unoccupied(n_row, n_col) and
                            not (n_row, n_col) in destinations):
                        ants.issue_order((a_row, a_col, new_direction))
                        new_lefty[(n_row, n_col)] = new_direction
                        destinations.append((n_row, n_col))
                        break
                    else:
                        # IMPROVEMENT: Try alternative directions when blocked
                        for alt_dir in [LEFT[new_direction], RIGHT[new_direction]]:
                            alt_row, alt_col = ants.destination(a_row, a_col, alt_dir)
                            if (ants.passable(alt_row, alt_col) and
                                    ants.unoccupied(alt_row, alt_col) and
                                    not (alt_row, alt_col) in destinations):
                                ants.issue_order((a_row, a_col, alt_dir))
                                new_lefty[(alt_row, alt_col)] = alt_dir
                                destinations.append((alt_row, alt_col))
                                break
                        else:
                            # have ant wait until it is clear
                            new_straight[(a_row, a_col)] = RIGHT[direction]
                            destinations.append((a_row, a_col))
                        break

if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    try:
        Ants.run(AdvancedBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')