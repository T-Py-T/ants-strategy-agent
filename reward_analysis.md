# Reward Function Analysis for Ants AI Challenge

## Current Rule-Based Strategy Analysis

### Implicit Reward Structure
Our current bot implements an implicit reward function through its priority system:

1. **Hill Return Priority** (Highest): Return to hill when ≤20 ants
2. **Food Collection Priority**: Hunt food within 30-50 tile radius
3. **Enemy Hill Attack Priority**: Attack enemy hills when advantageous
4. **Enemy Ant Hunt Priority**: Hunt enemy ants when we have numerical advantage
5. **Exploration Priority** (Lowest): Explore unseen areas

### Reward Function Design for RL

If we were to implement Reinforcement Learning, here's how we could structure the reward function:

```python
def calculate_reward(state, action, next_state):
    reward = 0.0
    
    # Primary objectives (high weight)
    ant_count_reward = (next_state.my_ants - state.my_ants) * 10.0
    food_collected_reward = (state.food_collected - next_state.food_collected) * 5.0
    enemy_ants_killed_reward = (state.enemy_ants - next_state.enemy_ants) * 15.0
    
    # Secondary objectives (medium weight)
    territory_control_reward = len(next_state.my_territory) - len(state.my_territory)
    enemy_hill_damage_reward = (state.enemy_hill_health - next_state.enemy_hill_health) * 20.0
    
    # Penalties (negative weight)
    ant_death_penalty = (state.my_ants - next_state.my_ants) * -5.0
    starvation_penalty = -1.0 if next_state.my_ants == 0 else 0.0
    
    # Exploration bonus (low weight)
    exploration_reward = len(next_state.explored_tiles) - len(state.explored_tiles)
    
    reward = (ant_count_reward + food_collected_reward + enemy_ants_killed_reward + 
             territory_control_reward + enemy_hill_damage_reward + 
             ant_death_penalty + starvation_penalty + exploration_reward * 0.1)
    
    return reward
```

### Potential RL Failure Modes

#### 1. Greedy Food Collection (Local Optima)
**Problem**: RL agent might learn to collect all food without returning to hill
- **Current Protection**: Our rule-based system forces hill return when ≤20 ants
- **RL Risk**: Agent might optimize for immediate food reward, ignoring multiplication
- **Mitigation**: Add strong penalty for not multiplying when ant count is low

#### 2. Over-Aggressive Combat
**Problem**: Agent might attack enemy ants when outnumbered
- **Current Protection**: We only hunt when `len(my_ants) > len(enemy_ants)`
- **RL Risk**: Agent might learn to attack regardless of odds
- **Mitigation**: Add negative reward for losing ants in combat

#### 3. Exploration vs Exploitation Trade-off
**Problem**: Agent might either over-explore or under-explore
- **Current Protection**: Balanced priority system with food hunting taking precedence
- **RL Risk**: Agent might get stuck in exploration or ignore new areas entirely
- **Mitigation**: Dynamic exploration bonus based on game phase

#### 4. Short-term vs Long-term Optimization
**Problem**: Agent might optimize for immediate rewards over long-term strategy
- **Current Protection**: Our standing orders system maintains long-term objectives
- **RL Risk**: Agent might abandon long-term goals for immediate gains
- **Mitigation**: Use discount factor and reward shaping for long-term value

### State Space Design

```python
class GameState:
    def __init__(self):
        # Agent state
        self.my_ants = []
        self.my_hills = []
        self.food_collected = 0
        
        # Environment state
        self.enemy_ants = []
        self.enemy_hills = []
        self.food_locations = []
        self.explored_tiles = set()
        
        # Game metrics
        self.turn_count = 0
        self.territory_control = 0
        self.ant_efficiency = 0.0
```

### Action Space Design

```python
class ActionSpace:
    def __init__(self):
        # Movement actions
        self.MOVE_NORTH = 0
        self.MOVE_SOUTH = 1
        self.MOVE_EAST = 2
        self.MOVE_WEST = 3
        self.STAY = 4
        
        # Strategic actions
        self.RETURN_TO_HILL = 5
        self.HUNT_FOOD = 6
        self.HUNT_ENEMY = 7
        self.EXPLORE = 8
        self.DEFEND_HILL = 9
```

### Reward Shaping Techniques

1. **Potential-Based Shaping**: Use potential functions to guide learning
2. **Curriculum Learning**: Start with simple scenarios, gradually increase complexity
3. **Multi-Objective Optimization**: Balance competing objectives using Pareto optimization
4. **Hierarchical RL**: Separate high-level strategy from low-level execution

### Evaluation Metrics

- **Win Rate**: Percentage of games won against each opponent type
- **Ant Efficiency**: Ants produced per food collected
- **Territory Control**: Percentage of map controlled
- **Survival Rate**: Average game length before elimination
- **Resource Utilization**: Food collection rate and hill return frequency

This analysis demonstrates the complexity of designing reward functions for multi-objective, long-horizon problems - a key challenge in AI engineering.
