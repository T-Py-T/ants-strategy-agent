# AntsAIBot Testing Makefile
# Provides easy commands for testing your bot against various opponents

.PHONY: help install test test-quick test-full test-against-samples test-against-random test-against-hunter test-against-greedy test-against-lefty test-self test-visualize clean docker-build docker-test docker-run stats stats-json stats-parallel

# Default target
help:
	@echo "AntsAIBot Testing Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install          Install Python dependencies"
	@echo "  docker-build     Build Docker image for testing"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run quick test (30 turns, 2 players)"
	@echo "  test-quick       Run quick test with your bot vs random"
	@echo "  test-full        Run full test (1000 turns, 4 players)"
	@echo "  test-self        Test your bot against itself (4 players)"
	@echo "  test-against-samples  Test against all sample bots"
	@echo "  test-probabilistic   Run 10 games per opponent, calculate win rates"
	@echo "  test-against-random   Test against RandomBot"
	@echo "  test-against-hunter   Test against HunterBot"
	@echo "  test-against-greedy   Test against GreedyBot"
	@echo "  test-against-lefty    Test against LeftyBot"
	@echo ""
	@echo "Statistical Analysis:"
	@echo "  stats            Run statistical analysis (default: 10 games, 1000 turns)"
	@echo "  stats-json       Run JSON-based statistical analysis (default: 10 games, 1000 turns)"
	@echo "  stats-parallel   Run parallel statistical analysis (default: 100 games, 10 parallel)"
	@echo "  stats GAMES=5 TURNS=500    Run with custom parameters"
	@echo "  stats-json GAMES=20 TURNS=2000  Run JSON analysis with custom parameters"
	@echo "  stats-parallel GAMES=500 PARALLEL=20  Run parallel analysis with custom parameters"
	@echo ""
	@echo "Analysis:"
	@echo "  analyze            Fast analysis (20 games + stats)"
	@echo "  validate           Validate raw outputs against fast analysis"
	@echo ""
	@echo "Visualization:"
	@echo "  test-visualize   Run test with live visualization"
	@echo "  visualize-latest Visualize the most recent game replay"
	@echo ""
	@echo "Docker:"
	@echo "  docker-test      Run tests in Docker container"
	@echo "  docker-run       Run interactive Docker container"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean            Clean game logs and temporary files"

# Install dependencies
install:
	@echo "Checking if dependencies are available..."
	@python3 -c "import colorama, pytest" 2>/dev/null && echo "Dependencies already available" || (echo "Installing dependencies..." && pip3 install --break-system-packages colorama pytest)

# Build Docker image
docker-build:
	docker build -t antsaibot .

# Run tests in Docker
docker-test:
	docker run --rm -v $(PWD)/game_logs:/app/game_logs antsaibot make test

# Run interactive Docker container
docker-run:
	docker run -it --rm -v $(PWD):/app -w /app antsaibot /bin/bash

# Quick test (30 turns, 2 players)
test:
	@echo "Running quick test (30 turns, 2 players)..."
	PYTHONPATH=. python3 src/tools/playgame.py \
		--engine_seed 42 \
		--player_seed 42 \
		--end_wait=0.25 \
		--verbose \
		--log_dir game_logs \
		--turns 30 \
		--map_file maps/maze/maze_02p_01.map \
		"python3 src/bots/bot.py" \
		"python3 src/sample_bots/python/RandomBot.py"

# Quick test with your bot vs random
test-quick: test

# Full test (1000 turns, 4 players)
test-full:
	@echo "Running full test (1000 turns, 4 players)..."
	PYTHONPATH=. python3 src/tools/playgame.py \
		--player_seed 42 \
		--end_wait=0.25 \
		--verbose \
		--log_dir game_logs \
		--turns 1000 \
		--map_file maps/maze/maze_04p_01.map \
		"python3 src/bots/bot.py" \
		"python3 src/sample_bots/python/RandomBot.py" \
		"python3 src/sample_bots/python/HunterBot.py" \
		"python3 src/sample_bots/python/GreedyBot.py"

# Test your bot against itself (4 players)
test-self:
	@echo "Testing bot against itself (4 players)..."
	PYTHONPATH=. python3 src/tools/playgame.py \
		--player_seed 42 \
		--end_wait=0.25 \
		--verbose \
		--log_dir game_logs \
		--turns 1000 \
		--map_file maps/maze/maze_04p_01.map \
		"python3 src/bots/bot.py" \
		"python3 src/bots/bot.py" \
		"python3 src/bots/bot.py" \
		"python3 src/bots/bot.py"

# Advanced test - vs LeftyBot (wall-following strategy)
test-vs-lefty:
	@echo "Testing vs LeftyBot (wall-following strategy)..."
	PYTHONPATH=. python3 src/tools/playgame.py \
		--player_seed 42 \
		--end_wait=0.25 \
		--verbose \
		--log_dir game_logs \
		--turns 500 \
		--map_file maps/maze/maze_02p_01.map \
		"python3 src/bots/bot.py" \
		"python3 src/sample_bots/python/LeftyBot.py"

# Advanced test - vs multiple advanced bots
test-vs-advanced:
	@echo "Testing vs multiple advanced bots..."
	PYTHONPATH=. python3 src/tools/playgame.py \
		--player_seed 42 \
		--end_wait=0.25 \
		--verbose \
		--log_dir game_logs \
		--turns 1000 \
		--map_file maps/maze/maze_04p_01.map \
		"python3 src/bots/bot.py" \
		"python3 src/sample_bots/python/LeftyBot.py" \
		"python3 src/sample_bots/python/HunterBot.py" \
		"python3 src/sample_bots/python/GreedyBot.py"

# Challenge test - vs Java HunterBot (compiled)
test-vs-java:
	@echo "Testing vs Java HunterBot..."
	cd src/sample_bots/java && make
	PYTHONPATH=. python3 src/tools/playgame.py \
		--player_seed 42 \
		--end_wait=0.25 \
		--verbose \
		--log_dir game_logs \
		--turns 500 \
		--map_file maps/maze/maze_02p_01.map \
		"python3 src/bots/bot.py" \
		"java -cp src/sample_bots/java HunterBot"

# Ultimate challenge - all advanced bots
test-ultimate:
	@echo "Ultimate challenge - vs all advanced bots..."
	cd src/sample_bots/java && make
	PYTHONPATH=. python3 src/tools/playgame.py \
		--player_seed 42 \
		--end_wait=0.25 \
		--verbose \
		--log_dir game_logs \
		--turns 1000 \
		--map_file maps/maze/maze_04p_01.map \
		"python3 src/bots/bot.py" \
		"python3 src/sample_bots/python/LeftyBot.py" \
		"python3 src/sample_bots/python/HunterBot.py" \
		"java -cp src/sample_bots/java HunterBot"

# Test against RandomBot
test-against-random:
	@echo "Testing against RandomBot..."
	PYTHONPATH=. python3 src/tools/playgame.py \
		--player_seed 42 \
		--end_wait=0.25 \
		--verbose \
		--log_dir game_logs \
		--turns 1000 \
		--map_file maps/maze/maze_02p_01.map \
		"python3 src/bots/bot.py" \
		"python3 src/sample_bots/python/RandomBot.py"

# Test against HunterBot
test-against-hunter:
	@echo "Testing against HunterBot..."
	PYTHONPATH=. python3 src/tools/playgame.py \
		--player_seed 42 \
		--end_wait=0.25 \
		--verbose \
		--log_dir game_logs \
		--turns 1000 \
		--map_file maps/maze/maze_02p_01.map \
		"python3 src/bots/bot.py" \
		"python3 src/sample_bots/python/HunterBot.py"

# Test against GreedyBot
test-against-greedy:
	@echo "Testing against GreedyBot..."
	PYTHONPATH=. python3 src/tools/playgame.py \
		--player_seed 42 \
		--end_wait=0.25 \
		--verbose \
		--log_dir game_logs \
		--turns 1000 \
		--map_file maps/maze/maze_02p_01.map \
		"python3 src/bots/bot.py" \
		"python3 src/sample_bots/python/GreedyBot.py"

# Test against LeftyBot
test-against-lefty:
	@echo "Testing against LeftyBot..."
	PYTHONPATH=. python3 src/tools/playgame.py \
		--player_seed 42 \
		--end_wait=0.25 \
		--verbose \
		--log_dir game_logs \
		--turns 1000 \
		--map_file maps/maze/maze_02p_01.map \
		"python3 src/bots/bot.py" \
		"python3 src/sample_bots/python/LeftyBot.py"

# Test against all sample bots
test-against-samples:
	@echo "Testing against all sample bots..."
	@$(MAKE) test-against-random
	@$(MAKE) test-against-hunter
	@$(MAKE) test-against-greedy
	@$(MAKE) test-against-lefty

# Probabilistic testing - run multiple games and calculate success rates
test-probabilistic:
	@echo "Running probabilistic testing (10 games per opponent)..."
	@echo "=================================================="
	@$(MAKE) test-prob-random 2>/dev/null
	@$(MAKE) test-prob-hunter 2>/dev/null
	@$(MAKE) test-prob-greedy 2>/dev/null
	@$(MAKE) test-prob-lefty 2>/dev/null
	@echo "=================================================="
	@echo "Probabilistic testing complete!"

# Probabilistic test against RandomBot (10 games)
test-prob-random:
	@echo "Testing vs RandomBot (10 games)..."
	@GAMES=0; WINS=0; LOSSES=0; DRAWS=0; \
	for i in $$(seq 1 10); do \
		echo "  Game $$i/10..."; \
		RESULT=$$(PYTHONPATH=. python3 src/tools/playgame.py \
			--player_seed $$(($$RANDOM % 10000)) \
			--end_wait=0.0 \
			--log_dir game_logs \
			--turns 1000 \
			--map_file maps/maze/maze_02p_01.map \
			"python3 src/bots/bot.py" \
			"python3 src/sample_bots/python/RandomBot.py" 2>/dev/null | \
			tail -1 | grep -o "score [0-9]* [0-9]*"); \
		if [ -n "$$RESULT" ]; then \
			MY_SCORE=$$(echo $$RESULT | awk '{print $$2}'); \
			THEIR_SCORE=$$(echo $$RESULT | awk '{print $$3}'); \
		else \
			MY_SCORE=0; \
			THEIR_SCORE=0; \
		fi; \
		GAMES=$$((GAMES + 1)); \
		if [ "$$MY_SCORE" -gt "$$THEIR_SCORE" ]; then \
			WINS=$$((WINS + 1)); \
		elif [ "$$MY_SCORE" -lt "$$THEIR_SCORE" ]; then \
			LOSSES=$$((LOSSES + 1)); \
		else \
			DRAWS=$$((DRAWS + 1)); \
		fi; \
	done; \
	WIN_RATE=$$(echo "scale=1; $$WINS * 100 / $$GAMES" | bc); \
	echo "RandomBot: $$WINS wins, $$LOSSES losses, $$DRAWS draws ($$WIN_RATE% win rate)"

# Probabilistic test against HunterBot (10 games)
test-prob-hunter:
	@echo "Testing vs HunterBot (10 games)..."
	@GAMES=0; WINS=0; LOSSES=0; DRAWS=0; \
	for i in $$(seq 1 10); do \
		echo "  Game $$i/10..."; \
		RESULT=$$(PYTHONPATH=. python3 src/tools/playgame.py \
			--player_seed $$(($$RANDOM % 10000)) \
			--end_wait=0.0 \
			--log_dir game_logs \
			--turns 1000 \
			--map_file maps/maze/maze_02p_01.map \
			"python3 src/bots/bot.py" \
			"python3 src/sample_bots/python/HunterBot.py" 2>/dev/null | \
			tail -1 | grep -o "score [0-9]* [0-9]*"); \
		if [ -n "$$RESULT" ]; then \
			MY_SCORE=$$(echo $$RESULT | awk '{print $$2}'); \
			THEIR_SCORE=$$(echo $$RESULT | awk '{print $$3}'); \
		else \
			MY_SCORE=0; \
			THEIR_SCORE=0; \
		fi; \
		GAMES=$$((GAMES + 1)); \
		if [ "$$MY_SCORE" -gt "$$THEIR_SCORE" ]; then \
			WINS=$$((WINS + 1)); \
		elif [ "$$MY_SCORE" -lt "$$THEIR_SCORE" ]; then \
			LOSSES=$$((LOSSES + 1)); \
		else \
			DRAWS=$$((DRAWS + 1)); \
		fi; \
	done; \
	WIN_RATE=$$(echo "scale=1; $$WINS * 100 / $$GAMES" | bc); \
	echo "HunterBot: $$WINS wins, $$LOSSES losses, $$DRAWS draws ($$WIN_RATE% win rate)"

# Probabilistic test against GreedyBot (10 games)
test-prob-greedy:
	@echo "Testing vs GreedyBot (10 games)..."
	@GAMES=0; WINS=0; LOSSES=0; DRAWS=0; \
	for i in $$(seq 1 10); do \
		echo "  Game $$i/10..."; \
		RESULT=$$(PYTHONPATH=. python3 src/tools/playgame.py \
			--player_seed $$(($$RANDOM % 10000)) \
			--end_wait=0.0 \
			--log_dir game_logs \
			--turns 1000 \
			--map_file maps/maze/maze_02p_01.map \
			"python3 src/bots/bot.py" \
			"python3 src/sample_bots/python/GreedyBot.py" 2>/dev/null | \
			tail -1 | grep -o "score [0-9]* [0-9]*"); \
		if [ -n "$$RESULT" ]; then \
			MY_SCORE=$$(echo $$RESULT | awk '{print $$2}'); \
			THEIR_SCORE=$$(echo $$RESULT | awk '{print $$3}'); \
		else \
			MY_SCORE=0; \
			THEIR_SCORE=0; \
		fi; \
		GAMES=$$((GAMES + 1)); \
		if [ "$$MY_SCORE" -gt "$$THEIR_SCORE" ]; then \
			WINS=$$((WINS + 1)); \
		elif [ "$$MY_SCORE" -lt "$$THEIR_SCORE" ]; then \
			LOSSES=$$((LOSSES + 1)); \
		else \
			DRAWS=$$((DRAWS + 1)); \
		fi; \
	done; \
	WIN_RATE=$$(echo "scale=1; $$WINS * 100 / $$GAMES" | bc); \
	echo "GreedyBot: $$WINS wins, $$LOSSES losses, $$DRAWS draws ($$WIN_RATE% win rate)"

# Probabilistic test against LeftyBot (10 games)
test-prob-lefty:
	@echo "Testing vs LeftyBot (10 games)..."
	@GAMES=0; WINS=0; LOSSES=0; DRAWS=0; \
	for i in $$(seq 1 10); do \
		echo "  Game $$i/10..."; \
		RESULT=$$(PYTHONPATH=. python3 src/tools/playgame.py \
			--player_seed $$(($$RANDOM % 10000)) \
			--end_wait=0.0 \
			--log_dir game_logs \
			--turns 1000 \
			--map_file maps/maze/maze_02p_01.map \
			"python3 src/bots/bot.py" \
			"python3 src/sample_bots/python/LeftyBot.py" 2>/dev/null | \
			tail -1 | grep -o "score [0-9]* [0-9]*"); \
		if [ -n "$$RESULT" ]; then \
			MY_SCORE=$$(echo $$RESULT | awk '{print $$2}'); \
			THEIR_SCORE=$$(echo $$RESULT | awk '{print $$3}'); \
		else \
			MY_SCORE=0; \
			THEIR_SCORE=0; \
		fi; \
		GAMES=$$((GAMES + 1)); \
		if [ "$$MY_SCORE" -gt "$$THEIR_SCORE" ]; then \
			WINS=$$((WINS + 1)); \
		elif [ "$$MY_SCORE" -lt "$$THEIR_SCORE" ]; then \
			LOSSES=$$((LOSSES + 1)); \
		else \
			DRAWS=$$((DRAWS + 1)); \
		fi; \
	done; \
	WIN_RATE=$$(echo "scale=1; $$WINS * 100 / $$GAMES" | bc); \
	echo "LeftyBot: $$WINS wins, $$LOSSES losses, $$DRAWS draws ($$WIN_RATE% win rate)"

# Test with live visualization
test-visualize:
	@echo "Running test with live visualization..."
	PYTHONPATH=. python3 src/tools/playgame.py \
		-So \
		--player_seed 42 \
		--end_wait=0.25 \
		--verbose \
		--log_dir game_logs \
		--turns 1000 \
		--map_file maps/maze/maze_04p_01.map \
		"python3 src/bots/bot.py" \
		"python3 src/sample_bots/python/RandomBot.py" \
		"python3 src/sample_bots/python/HunterBot.py" \
		"python3 src/sample_bots/python/GreedyBot.py" | \
	java -jar visualizer/visualizer.jar

# Visualize the most recent game replay
visualize-latest:
	@echo "Visualizing latest game replay..."
	@LATEST_REPLAY=$$(ls -t game_logs/*.replay 2>/dev/null | head -1); \
	if [ -n "$$LATEST_REPLAY" ]; then \
		python3 visualizer/visualize_locally.py "$$LATEST_REPLAY"; \
	else \
		echo "No replay files found in game_logs/"; \
	fi

# Statistical Analysis Commands
# Default values
GAMES ?= 10
TURNS ?= 1000

# Run statistical analysis with customizable parameters
stats:
	@echo "Running statistical analysis..."
	@echo "Games per opponent: $(GAMES)"
	@echo "Turns per game: $(TURNS)"
	@echo ""
	@GAMES_PER_TEST=$(GAMES) ./scripts/run_statistics.sh

# Run JSON-based statistical analysis with customizable parameters
stats-json:
	@echo "Running JSON-based statistical analysis..."
	@echo "Games per opponent: $(GAMES)"
	@echo "Turns per game: $(TURNS)"
	@echo ""
	@GAMES_PER_TEST=$(GAMES) TURNS_PER_GAME=$(TURNS) ./scripts/run_statistics_json.sh

# Quick statistical analysis (5 games, 500 turns)
stats-quick:
	@echo "Running quick statistical analysis..."
	@$(MAKE) stats GAMES=5 TURNS=500

# full statistical analysis (20 games, 2000 turns)
stats-full:
	@echo "Running full statistical analysis..."
	@$(MAKE) stats-json GAMES=20 TURNS=2000

# Run parallel statistical analysis with customizable parameters
stats-parallel:
	@echo "Running parallel statistical analysis..."
	@echo "Games per opponent: $(GAMES)"
	@echo "Turns per game: $(TURNS)"
	@echo "Max parallel: $(PARALLEL)"
	@echo ""
	@GAMES_PER_TEST=$(GAMES) TURNS_PER_GAME=$(TURNS) MAX_PARALLEL=$(PARALLEL) ./scripts/run_parallel_stats.sh

# High-speed parallel analysis (500 games, 20 parallel)
stats-fast:
	@echo "Running high-speed parallel analysis..."
	@$(MAKE) stats-parallel GAMES=500 PARALLEL=20

# Massive parallel analysis (1000 games, 50 parallel)
stats-massive:
	@echo "Running massive parallel analysis..."
	@$(MAKE) stats-parallel GAMES=1000 PARALLEL=50

# Analysis Commands
# Install analysis dependencies
install-analysis:
	@echo "Installing analysis dependencies with uv..."
	uv add pandas numpy matplotlib seaborn scipy

# Fast analysis (20 games + stats)
analyze:
	@echo "Running fast analysis (20 games + stats)..."
	@$(MAKE) stats-json GAMES=20
	@echo "Analyzing results..."
	uv run python scripts/analyze_results.py --file parallel_statistics.json

# Validate raw against fast output
validate:
	@echo "Validating raw outputs against fast analysis..."
	@$(MAKE) stats-json GAMES=20
	uv run python scripts/analyze_results.py --file parallel_statistics.json --validate --sample-size 5

# Clean up game logs and temporary files
clean:
	@echo "Cleaning up game logs and temporary files..."
	rm -rf game_logs/*.replay
	rm -rf game_logs/*.html
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf src/ants/__pycache__
	rm -rf src/bots/__pycache__
	rm -rf src/tools/__pycache__
	rm -rf src/sample_bots/__pycache__
	rm -rf visualizer/__pycache__
