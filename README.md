# Ants AI Bot: Multi-Agent Strategy Implementation

**A competitive AI bot for the Ants AI Challenge implementing hierarchical decision-making and strategic optimization**

I built this bot to compete in the Ants AI Challenge, focusing on creating an intelligent agent that can make strategic decisions in real-time while managing multiple competing objectives. The challenge requires balancing food collection, colony expansion, territory control, and enemy engagement - essentially a multi-objective optimization problem with dynamic constraints.

## What I Built

### Core Decision System
I implemented a hierarchical priority system that balances competing objectives:
- **Colony multiplication** (highest priority) - ensuring ants return to hills for reproduction
- **Strategic combat** - targeting enemy hills and ants when advantageous  
- **Resource acquisition** - aggressive food collection with dynamic distance thresholds
- **Exploration** - systematic map discovery using wall-following algorithms

### Key Algorithms
**Multi-Objective Optimization**: The bot uses a priority-based decision tree where each ant evaluates multiple objectives and selects the highest-priority action available. This prevents getting stuck in local optima (like collecting all food without reproducing).

**Dynamic Thresholding**: Food hunting distances adapt based on colony size - when I have fewer ants, the bot hunts food from much further away (up to 50 tiles) to catch up to opponents.

**Pathfinding & Navigation**: Uses breadth-first search for optimal pathfinding and implements wall-following exploration patterns adapted from computational geometry principles.

**State Management**: Tracks game state efficiently using dictionaries and sets, with a standing orders system that persists tasks across multiple turns.

### Technical Implementation
The bot combines insights from studying successful opponents (LeftyBot's exploration, GreedyBot's priority system) with my own optimizations:

- **Aggressive multiplication strategy** - returns to hills when ant count ≤ 20
- **Strategic combat** - only hunts enemy ants when I have numerical advantage
- **Enhanced exploration** - multiple exploration patterns beyond simple wall-following
- **Efficient collision avoidance** - prevents multiple ants from targeting the same destination

## Current Status & Performance

The bot is functional but still underperforming against advanced opponents. Here's what I've learned:

### What Works
- **Hill return mechanics** - Fixed a critical bug where ants collected food but didn't return to hills for multiplication
- **Aggressive food hunting** - Extended hunting distances to 50+ tiles when colony is small
- **Strategic combat** - Only engages enemies when I have numerical advantage
- **Exploration patterns** - Multiple exploration strategies beyond basic wall-following

### Current Challenges
- **Performance against LeftyBot** - Still losing to systematic wall-following exploration
- **Food collection efficiency** - GreedyBot's direct food collection strategy outperforms my approach
- **Multi-objective balance** - Need better tuning of priority weights and thresholds

### Performance Metrics
| Opponent | Result | Key Issue |
|----------|--------|-----------|
| RandomBot | TBD | Baseline testing needed |
| GreedyBot | Loss (16 vs 31 ants) | Food collection strategy needs work |
| HunterBot | Loss (6 vs 4 ants) | Combat mechanics need refinement |
| LeftyBot | Loss (11 vs 52 ants) | Exploration strategy needs improvement |

## Testing & Evaluation

I built a comprehensive testing framework to systematically evaluate performance:

### Testing Infrastructure
- **Probabilistic testing** - Run 10+ games per opponent to calculate win rates
- **Performance benchmarking** - Track ant efficiency, territory control, resource utilization
- **Game replay analysis** - Visualize bot behavior and identify improvement areas
- **Automated test suite** - Makefile commands for consistent testing

### Reward Function Analysis
I documented the implicit reward structure in `reward_analysis.md` and designed a framework for potential reinforcement learning:

```python
def calculate_reward(state, action, next_state):
    reward = 0.0
    
    # Primary objectives
    ant_count_reward = (next_state.my_ants - state.my_ants) * 10.0
    food_collected_reward = (state.food_collected - next_state.food_collected) * 5.0
    enemy_ants_killed_reward = (state.enemy_ants - next_state.enemy_ants) * 15.0
    
    # Penalties
    ant_death_penalty = (state.my_ants - next_state.my_ants) * -5.0
    starvation_penalty = -1.0 if next_state.my_ants == 0 else 0.0
    
    return reward
```

## Next Steps

### Immediate Improvements
1. **Better exploration strategy** - Study LeftyBot's wall-following more carefully
2. **Food collection optimization** - Analyze GreedyBot's efficiency techniques  
3. **Combat mechanics** - Improve enemy ant hunting and hill targeting
4. **Threshold tuning** - Optimize distance thresholds and priority weights

### Future Development
1. **Reinforcement Learning** - Implement the reward function framework I designed
2. **Neural Networks** - Use the state space architecture for deep learning
3. **Self-play training** - Multi-agent learning with multiple bot instances
4. **Transfer learning** - Adapt strategies across different map configurations

## Getting Started

### Setup
```bash
git clone <repository-url>
cd AntsAIBot
make install              # Install dependencies
make test-full           # Run evaluation suite
make visualize-latest    # View results
```

### Testing
```bash
# Run comprehensive tests
make test-probabilistic    # Statistical analysis
make test-against-samples  # Multi-opponent testing
make benchmark            # Performance benchmarking

# Test against specific opponents
make test-against-random   # Baseline
make test-against-greedy   # Food collection
make test-against-hunter   # Combat
```

### Development
```bash
# Docker environment
make docker-build
make docker-test

# VS Code Dev Container
# Open in VS Code → "Dev Containers: Reopen in Container"
```

## Project Structure

```
AntsAIBot/
├── src/
│   ├── ants/           # Game engine
│   ├── bots/           # My bot implementation
│   └── tools/          # Testing and analysis tools
├── visualizer/         # Game replay visualization
├── scripts/            # Testing scripts
├── maps/              # Game maps
└── game_logs/         # Test results and replays
```

---

For more details on the Ants AI Challenge, see the [official tutorial](http://ants.aichallenge.org/ants_tutorial.php).