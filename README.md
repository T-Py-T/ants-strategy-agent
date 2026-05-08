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
| RandomBot | Win (deterministic baseline) | RandomBot dies / hangs out — bot reliably wins |
| GreedyBot | Loss (16 vs 31 ants) | Food collection strategy needs work |
| HunterBot | Loss (6 vs 4 ants) | Combat mechanics need refinement |
| LeftyBot | Loss (11 vs 52 ants) | Exploration strategy needs improvement |
| **XathisBot** | **Loss (final boss)** | Port of the AI Challenge 2011 winner — see below |

### The "Final Boss": XathisBot

`src/bots/xathis_bot.py` is a Python port of the **AI Challenge 2011 winner**
("xathis", written in Java). The original source and the recovered postmortem
live at `docs/reference/xathis/`. xathis uses the same general phases as a
strong scripted bot (food BFS, exploration, hill attack, defence) but adds
two things that pushed it past every other entry in the world:

1. **Diffusion-based exploration** — every tile accumulates a "fog" value over
   time; ants are pulled toward the highest-value frontier (`_init_explore`
   + `_explore`).
2. **Group-based combat with minimax** — ants in mutual gamma-distance form a
   "fight group"; we exhaustively search every (my_combo × enemy_combo) and
   pick the move that maximises `(enemy_dead − my_dead)` under the official
   battle-resolution rule (`_fight`).

Empirical (3 games × 500 turns on `random_walk_02p_01`):

| Opponent | XathisBot wins | XathisBot losses | Draws |
|----------|---:|---:|---:|
| RandomBot | 3 | 0 | 0 |
| HoldBot   | 3 | 0 | 0 |
| HunterBot | 3 | 0 | 0 |
| GreedyBot | 3 | 0 | 0 |
| LeftyBot  | 3 | 0 | 0 |
| 4-Player  | 3 | 0 | 0 |

That's the bar: any successor (the ML/RL bot you're planning) must beat
xathis_bot to be world-class. Try it yourself:

```bash
make test-vs-xathis      # one head-to-head game with replay
make benchmark-xathis    # full benchmark suite, xathis under test
```

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
The project uses [`uv`](https://docs.astral.sh/uv/) as the canonical
package manager (with `pip` as a fallback). Dependencies are declared in
`pyproject.toml`; lock state lives in `uv.lock`.

```bash
git clone <repository-url>
cd AntsAIBot

# One-step install (uses uv if available, falls back to pip + venv).
make install

# Or, manually:
uv sync --all-extras                      # canonical
# pip install -e ".[dev]"                 # fallback

make test                # Run a quick 30-turn integration game
make pytest              # Run the unit-test suite (~140 tests)
make visualize-latest    # Open the latest replay in your browser
```

The project ships three optional dependency extras:

| Extra | What it adds | When you need it |
|-------|--------------|------------------|
| `[test]` | `pytest`, `pytest-cov` | Running the unit-test suite |
| `[analysis]` | `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy` | Running `scripts/analyze_results.py` and statistical analysis Make targets |
| `[dev]` | Both of the above | Local development |

### Testing
```bash
# Unit tests (fast — uses pytest)
make pytest                 # Full suite
make pytest-quick           # Skip subprocess sample-bot tests
make pytest-coverage        # With coverage report

# Integration testing (real games)
make test-probabilistic     # Statistical analysis (10 games per opponent)
make test-against-samples   # Multi-opponent testing
make benchmark              # Performance benchmarking

# Test against specific opponents
make test-against-random    # Baseline
make test-against-greedy    # Food collection
make test-against-hunter    # Combat
```

### Development
```bash
# Docker environment
make docker-build
make docker-test

# VS Code Dev Container
# Open in VS Code → "Dev Containers: Reopen in Container"
# (auto-runs `uv sync --all-extras` on first start)
```

### Continuous Integration
Every push and pull request runs the full pytest matrix on Python 3.11 /
3.12 / 3.13, plus a real-game integration check (`make test`) and a
Docker image build/run smoke test, via `.github/workflows/ci.yml`.

## Project Structure

```
AntsAIBot/
├── .devcontainer/       # VS Code Dev Container configuration
├── .github/workflows/   # GitHub Actions CI (pytest matrix + integration + docker)
├── src/
│   ├── ants/            # Game engine (Ants, Game, sandbox, run_game)
│   ├── bots/            # AdvancedBot — my bot implementation
│   ├── sample_bots/     # Reference opponents (Python / Java / C# / PHP)
│   └── tools/
│       ├── playgame.py  # Engine driver / runner
│       └── mapgen/      # Map-generation utilities
├── tests/               # pytest suite (unit + structural backstops)
├── visualizer/          # Game replay visualization
├── scripts/             # Statistical-analysis + benchmarking scripts
├── maps/                # Game maps (example, maze, multi_hill_maze, random_walk)
├── submission_test/     # Submission packaging sandbox
├── game_logs/           # Test outputs and game replays
├── pyproject.toml       # Project metadata, deps, extras, pytest config
├── uv.lock              # Pinned dependency resolution
├── Dockerfile           # Slim runtime image (Python 3.13 + JDK 21)
└── Makefile             # Friendly entry points for every workflow
```

---

For more details on the Ants AI Challenge, see the [official tutorial](http://ants.aichallenge.org/ants_tutorial.php).