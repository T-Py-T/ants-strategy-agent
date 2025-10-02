#!/bin/bash
# Benchmark script for AntsAIBot
# Runs multiple games and analyzes performance metrics

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_DIR="game_logs"
BENCHMARK_DIR="benchmark_results"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
GAMES_PER_TEST=5

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$BENCHMARK_DIR"

echo -e "${BLUE}AntsAIBot Benchmark Suite${NC}"
echo "============================="
echo "Timestamp: $TIMESTAMP"
echo "Games per test: $GAMES_PER_TEST"
echo ""

# Function to run benchmark test
run_benchmark() {
    local test_name="$1"
    local test_command="$2"
    local results_file="$BENCHMARK_DIR/${test_name}_${TIMESTAMP}.txt"
    
    echo -e "${YELLOW}Running benchmark: $test_name${NC}"
    echo "Benchmark: $test_name" > "$results_file"
    echo "Timestamp: $TIMESTAMP" >> "$results_file"
    echo "Games: $GAMES_PER_TEST" >> "$results_file"
    echo "Command: $test_command" >> "$results_file"
    echo "" >> "$results_file"
    
    local wins=0
    local losses=0
    local draws=0
    local total_turns=0
    local total_time=0
    
    for i in $(seq 1 $GAMES_PER_TEST); do
        echo -e "  Game $i/$GAMES_PER_TEST..."
        
        local start_time=$(date +%s.%N)
        
        # Run the game and capture output
        local game_output=$(eval "$test_command" 2>&1)
        local end_time=$(date +%s.%N)
        local game_time=$(echo "$end_time - $start_time" | bc)
        
        # Extract game results from output
        local turns=$(echo "$game_output" | grep -o "turn [0-9]* stats:" | tail -1 | grep -o "[0-9]*" || echo "0")
        
        # Extract scores and status
        local scores=$(echo "$game_output" | grep "^score " | tail -1 | sed 's/score //')
        local status=$(echo "$game_output" | grep "^status " | tail -1 | sed 's/status //')
        
        # Parse scores (our bot is player 0)
        local our_score=$(echo "$scores" | awk '{print $1}')
        local enemy_score=$(echo "$scores" | awk '{print $2}')
        
        # Parse status (our bot is player 0)
        local our_status=$(echo "$status" | awk '{print $1}')
        local enemy_status=$(echo "$status" | awk '{print $2}')
        
        # Determine winner based on scores and status
        if [ "$our_status" = "crashed" ] || [ "$our_status" = "timeout" ] || [ "$our_status" = "invalid" ]; then
            losses=$((losses + 1))
            result="LOSS"
        elif [ "$enemy_status" = "crashed" ] || [ "$enemy_status" = "timeout" ] || [ "$enemy_status" = "invalid" ]; then
            wins=$((wins + 1))
            result="WIN"
        elif [ "$our_score" -gt "$enemy_score" ]; then
            wins=$((wins + 1))
            result="WIN"
        elif [ "$enemy_score" -gt "$our_score" ]; then
            losses=$((losses + 1))
            result="LOSS"
        else
            draws=$((draws + 1))
            result="DRAW"
        fi
        
        total_turns=$((total_turns + turns))
        total_time=$(echo "$total_time + $game_time" | bc)
        
        echo "    Game $i: $result (${turns} turns, ${game_time}s)" >> "$results_file"
    done
    
    # Calculate averages
    local avg_turns=$(echo "scale=2; $total_turns / $GAMES_PER_TEST" | bc)
    local avg_time=$(echo "scale=2; $total_time / $GAMES_PER_TEST" | bc)
    local win_rate=$(echo "scale=2; $wins * 100 / $GAMES_PER_TEST" | bc)
    
    # Summary
    echo "" >> "$results_file"
    echo "SUMMARY:" >> "$results_file"
    echo "Wins: $wins" >> "$results_file"
    echo "Losses: $losses" >> "$results_file"
    echo "Draws: $draws" >> "$results_file"
    echo "Win Rate: ${win_rate}%" >> "$results_file"
    echo "Average Turns: $avg_turns" >> "$results_file"
    echo "Average Time: ${avg_time}s" >> "$results_file"
    
    echo -e "${GREEN}  Results: $wins wins, $losses losses, $draws draws (${win_rate}% win rate)${NC}"
    echo -e "  Average: ${avg_turns} turns, ${avg_time}s per game"
    echo ""
}

# Benchmark 1: vs RandomBot
run_benchmark "vs_RandomBot" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns 1000 --map_file maps/maze/maze_02p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/RandomBot.py' --nolaunch"

# Benchmark 2: vs HunterBot
run_benchmark "vs_HunterBot" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns 1000 --map_file maps/maze/maze_02p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/HunterBot.py' --nolaunch"

# Benchmark 3: vs GreedyBot
run_benchmark "vs_GreedyBot" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns 1000 --map_file maps/maze/maze_02p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/GreedyBot.py' --nolaunch"

# Benchmark 4: vs LeftyBot
run_benchmark "vs_LeftyBot" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns 1000 --map_file maps/maze/maze_02p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/LeftyBot.py' --nolaunch"

# Benchmark 5: Four-player game
run_benchmark "Four_Player" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns 1000 --map_file maps/maze/maze_04p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/RandomBot.py' 'python3 src/sample_bots/python/HunterBot.py' 'python3 src/sample_bots/python/GreedyBot.py' --nolaunch"

echo -e "${BLUE}Benchmark Complete${NC}"
echo "=================="
echo "Results saved to: $BENCHMARK_DIR/"
echo ""

# Generate summary report
SUMMARY_FILE="$BENCHMARK_DIR/summary_${TIMESTAMP}.txt"
echo "AntsAIBot Benchmark Summary - $TIMESTAMP" > "$SUMMARY_FILE"
echo "=======================================" >> "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"

for result_file in "$BENCHMARK_DIR"/*_${TIMESTAMP}.txt; do
    if [ -f "$result_file" ] && [ "$(basename "$result_file")" != "summary_${TIMESTAMP}.txt" ]; then
        echo "=== $(basename "$result_file") ===" >> "$SUMMARY_FILE"
        grep -E "(Wins:|Losses:|Draws:|Win Rate:|Average Turns:|Average Time:)" "$result_file" >> "$SUMMARY_FILE"
        echo "" >> "$SUMMARY_FILE"
    fi
done

echo "Summary report: $SUMMARY_FILE"
echo -e "${GREEN}Benchmark completed!${NC}"
