#!/bin/bash
# Statistics script for AntsAIBot
# Runs multiple games and shows only final statistics

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_DIR="game_logs"
STATS_FILE="statistics.txt"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
GAMES_PER_TEST=${GAMES_PER_TEST:-2}
TURNS_PER_GAME=${TURNS_PER_GAME:-1000}

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

echo -e "${BLUE}AntsAIBot Statistics Runner${NC}"
echo "=============================="
echo "Timestamp: $TIMESTAMP"
echo "Games per test: $GAMES_PER_TEST"
echo ""

# Function to run statistics test
run_statistics() {
    local test_name="$1"
    local test_command="$2"
    local results_file="$STATS_FILE"
    
    echo -e "${YELLOW}Running statistics: $test_name${NC}"
    echo "Statistics: $test_name" >> "$results_file"
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
        
        # Run the game and capture JSON output
        local game_json=$(eval "$test_command" 2>/dev/null)
        local end_time=$(date +%s.%N)
        local game_time=$(echo "$end_time - $start_time" | bc)
        
        # Check if JSON is valid and not empty
        if [ -z "$game_json" ] || ! echo "$game_json" | jq empty 2>/dev/null; then
            echo "    Game $i: ERROR (Invalid JSON output)" >> "$results_file"
            draws=$((draws + 1))
            result="ERROR"
            turns=0
            our_score=0
            enemy_score=0
            our_status="error"
            enemy_status="error"
        else
            # Parse JSON results using jq
            local our_score=$(echo "$game_json" | jq -r '.score[0] // 0')
            local enemy_score=$(echo "$game_json" | jq -r '.score[1] // 0')
            local our_status=$(echo "$game_json" | jq -r '.status[0] // "unknown"')
            local enemy_status=$(echo "$game_json" | jq -r '.status[1] // "unknown"')
            local turns=$(echo "$game_json" | jq -r '.game_length // 0')
            
            # Ensure we have valid numbers
            if [ "$our_score" = "null" ] || [ -z "$our_score" ]; then
                our_score=0
            fi
            if [ "$enemy_score" = "null" ] || [ -z "$enemy_score" ]; then
                enemy_score=0
            fi
            if [ "$turns" = "null" ] || [ -z "$turns" ]; then
                turns=0
            fi
            
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
        fi
        
        total_turns=$((total_turns + turns))
        total_time=$(echo "$total_time + $game_time" | bc)
        
        echo "    Game $i: $result (Score: $our_score vs $enemy_score, Status: $our_status vs $enemy_status, ${turns} turns, ${game_time}s)" >> "$results_file"
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
    echo "========================================" >> "$results_file"
    echo "" >> "$results_file"
    
    echo -e "${GREEN}  Results: $wins wins, $losses losses, $draws draws (${win_rate}% win rate)${NC}"
    echo -e "  Average: ${avg_turns} turns, ${avg_time}s per game"
    echo ""
}

# Initialize statistics file
echo "AntsAIBot Statistics Report - $TIMESTAMP" > "$STATS_FILE"
echo "=======================================" >> "$STATS_FILE"
echo "" >> "$STATS_FILE"

# Statistics 1: vs RandomBot
run_statistics "vs RandomBot" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns $TURNS_PER_GAME --map_file maps/maze/maze_02p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/RandomBot.py' --nolaunch --json"

# Statistics 2: vs HunterBot
run_statistics "vs HunterBot" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns $TURNS_PER_GAME --map_file maps/maze/maze_02p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/HunterBot.py' --nolaunch"

# Statistics 3: vs GreedyBot
run_statistics "vs GreedyBot" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns $TURNS_PER_GAME --map_file maps/maze/maze_02p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/GreedyBot.py' --nolaunch"

# Statistics 4: vs LeftyBot
run_statistics "vs LeftyBot" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns $TURNS_PER_GAME --map_file maps/maze/maze_02p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/LeftyBot.py' --nolaunch"

# Statistics 5: Four-player game
run_statistics "Four Player Game" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns $TURNS_PER_GAME --map_file maps/maze/maze_04p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/RandomBot.py' 'python3 src/sample_bots/python/HunterBot.py' 'python3 src/sample_bots/python/GreedyBot.py' --nolaunch"

echo -e "${BLUE}Statistics Complete${NC}"
echo "===================="
echo "Results saved to: $STATS_FILE"
echo ""

# Show summary
echo -e "${GREEN}Final Summary:${NC}"
echo "=============="
grep -E "(Statistics:|Wins:|Losses:|Draws:|Win Rate:)" "$STATS_FILE" | tail -20

echo ""
echo -e "${GREEN}Statistics completed!${NC}"
