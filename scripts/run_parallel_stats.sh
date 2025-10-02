#!/bin/bash
# Parallel statistics script for AntsAIBot
# Runs hundreds of games in parallel for fast statistical analysis

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_DIR="game_logs"
STATS_FILE="parallel_statistics.json"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
GAMES_PER_TEST=${GAMES_PER_TEST:-100}
TURNS_PER_GAME=${TURNS_PER_GAME:-1000}
MAX_PARALLEL=${MAX_PARALLEL:-10}  # Maximum parallel games

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

echo -e "${BLUE}AntsAIBot Parallel Statistics Runner${NC}"
echo "======================================="
echo "Timestamp: $TIMESTAMP"
echo "Games per test: $GAMES_PER_TEST"
echo "Turns per game: $TURNS_PER_GAME"
echo "Max parallel: $MAX_PARALLEL"
echo ""

# Function to run a single game and return JSON result
run_single_game() {
    local test_name="$1"
    local game_num="$2"
    local seed="$3"
    local turns="$4"
    local map_file="$5"
    local bot1="$6"
    local bot2="$7"
    
    local game_json=$(PYTHONPATH=. python3 src/tools/playgame.py \
        --player_seed "$seed" \
        --end_wait=0.1 \
        --log_dir "$LOG_DIR" \
        --turns "$turns" \
        --map_file "$map_file" \
        "$bot1" "$bot2" \
        --nolaunch --json 2>/dev/null)
    
    # Parse results
    local our_score=$(echo "$game_json" | jq -r '.score[0]')
    local enemy_score=$(echo "$game_json" | jq -r '.score[1]')
    local our_status=$(echo "$game_json" | jq -r '.status[0]')
    local enemy_status=$(echo "$game_json" | jq -r '.status[1]')
    local game_length=$(echo "$game_json" | jq -r '.game_length')
    
    # Determine result
    local result="DRAW"
    if [ "$our_status" = "crashed" ] || [ "$our_status" = "timeout" ] || [ "$our_status" = "invalid" ]; then
        result="LOSS"
    elif [ "$enemy_status" = "crashed" ] || [ "$enemy_status" = "timeout" ] || [ "$enemy_status" = "invalid" ]; then
        result="WIN"
    elif [ "$our_score" -gt "$enemy_score" ]; then
        result="WIN"
    elif [ "$enemy_score" -gt "$our_score" ]; then
        result="LOSS"
    fi
    
    # Output result as JSON
    echo "{\"test_name\": \"$test_name\", \"game\": $game_num, \"result\": \"$result\", \"our_score\": $our_score, \"enemy_score\": $enemy_score, \"our_status\": \"$our_status\", \"enemy_status\": \"$enemy_status\", \"turns\": $game_length}"
}

# Function to run parallel statistics test
run_parallel_statistics() {
    local test_name="$1"
    local map_file="$2"
    local bot1="$3"
    local bot2="$4"
    
    echo -e "${YELLOW}Running parallel statistics: $test_name${NC}"
    echo "  Games: $GAMES_PER_TEST, Parallel: $MAX_PARALLEL"
    
    local temp_file=$(mktemp)
    local pids=()
    local completed=0
    
    # Start games in parallel batches
    for i in $(seq 1 $GAMES_PER_TEST); do
        # Wait if we've reached max parallel
        while [ ${#pids[@]} -ge $MAX_PARALLEL ]; do
            for j in "${!pids[@]}"; do
                if ! kill -0 "${pids[j]}" 2>/dev/null; then
                    unset pids[j]
                    completed=$((completed + 1))
                    echo -ne "\r  Progress: $completed/$GAMES_PER_TEST games completed..."
                fi
            done
            sleep 0.1
        done
        
        # Start new game
        local seed=$((RANDOM % 10000))
        run_single_game "$test_name" "$i" "$seed" "$TURNS_PER_GAME" "$map_file" "$bot1" "$bot2" >> "$temp_file" &
        pids+=($!)
    done
    
    # Wait for all remaining games to complete
    for pid in "${pids[@]}"; do
        wait "$pid"
        completed=$((completed + 1))
        echo -ne "\r  Progress: $completed/$GAMES_PER_TEST games completed..."
    done
    echo ""
    
    # Process results
    local wins=0
    local losses=0
    local draws=0
    local total_turns=0
    
    while IFS= read -r line; do
        local result=$(echo "$line" | jq -r '.result')
        local turns=$(echo "$line" | jq -r '.turns')
        
        case "$result" in
            "WIN") wins=$((wins + 1)) ;;
            "LOSS") losses=$((losses + 1)) ;;
            "DRAW") draws=$((draws + 1)) ;;
        esac
        
        total_turns=$((total_turns + turns))
    done < "$temp_file"
    
    # Calculate averages
    local avg_turns=$(echo "scale=2; $total_turns / $GAMES_PER_TEST" | bc)
    local win_rate=$(echo "scale=2; $wins * 100 / $GAMES_PER_TEST" | bc)
    
    # Create JSON result for this test
    local test_json="{
        \"test_name\": \"$test_name\",
        \"timestamp\": \"$TIMESTAMP\",
        \"games\": $GAMES_PER_TEST,
        \"wins\": $wins,
        \"losses\": $losses,
        \"draws\": $draws,
        \"win_rate\": $win_rate,
        \"average_turns\": $avg_turns,
        \"max_parallel\": $MAX_PARALLEL
    }"
    
    # Append to results file
    if [ -f "$STATS_FILE" ]; then
        local temp_results=$(mktemp)
        echo "$test_json" > "$temp_results"
        jq '. + [input]' "$STATS_FILE" "$temp_results" > "${STATS_FILE}.tmp" && mv "${STATS_FILE}.tmp" "$STATS_FILE"
        rm "$temp_results"
    else
        echo "[$test_json]" > "$STATS_FILE"
    fi
    
    echo -e "${GREEN}  Results: $wins wins, $losses losses, $draws draws (${win_rate}% win rate)${NC}"
    echo -e "  Average: ${avg_turns} turns per game"
    echo ""
    
    rm "$temp_file"
}

# Initialize results file
echo "[]" > "$STATS_FILE"

# Run parallel statistics tests
run_parallel_statistics "vs RandomBot" \
    "maps/maze/maze_02p_01.map" \
    "python3 src/bots/bot.py" \
    "python3 src/sample_bots/python/RandomBot.py"

run_parallel_statistics "vs HunterBot" \
    "maps/maze/maze_02p_01.map" \
    "python3 src/bots/bot.py" \
    "python3 src/sample_bots/python/HunterBot.py"

run_parallel_statistics "vs GreedyBot" \
    "maps/maze/maze_02p_01.map" \
    "python3 src/bots/bot.py" \
    "python3 src/sample_bots/python/GreedyBot.py"

run_parallel_statistics "vs LeftyBot" \
    "maps/maze/maze_02p_01.map" \
    "python3 src/bots/bot.py" \
    "python3 src/sample_bots/python/LeftyBot.py"

echo -e "${BLUE}Parallel Statistics Complete${NC}"
echo "============================="
echo "Results saved to: $STATS_FILE"
echo ""

# Show summary using jq
echo -e "${GREEN}Final Summary:${NC}"
echo "=============="
jq -r '.[] | "\(.test_name): \(.wins) wins, \(.losses) losses, \(.draws) draws (\(.win_rate)% win rate)"' "$STATS_FILE"

echo ""
echo -e "${GREEN}Parallel statistics completed!${NC}"
echo ""
echo "You can analyze the results further with jq:"
echo "  jq '.[] | select(.test_name == \"vs RandomBot\")' $STATS_FILE"
echo "  jq '.[] | {test: .test_name, win_rate: .win_rate}' $STATS_FILE"
