#!/bin/bash
# Statistics script for AntsAIBot using JSON output
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
STATS_FILE="statistics.json"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
GAMES_PER_TEST=${GAMES_PER_TEST:-2}
TURNS_PER_GAME=${TURNS_PER_GAME:-1000}

# Check if yq is available
if ! command -v yq &> /dev/null; then
    echo -e "${RED}Error: yq is not installed. Please install yq to parse JSON output.${NC}"
    echo "Install with: brew install yq (on macOS) or visit https://github.com/mikefarah/yq"
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

echo -e "${BLUE}AntsAIBot Statistics Runner (JSON)${NC}"
echo "====================================="
echo "Timestamp: $TIMESTAMP"
echo "Games per test: $GAMES_PER_TEST"
echo ""

# Function to run statistics test
run_statistics() {
    local test_name="$1"
    local test_command="$2"
    local results_file="$STATS_FILE"
    
    echo -e "${YELLOW}Running statistics: $test_name${NC}"
    
    local wins=0
    local losses=0
    local draws=0
    local total_turns=0
    local total_time=0
    local game_results=()
    
    for i in $(seq 1 $GAMES_PER_TEST); do
        echo -e "  Game $i/$GAMES_PER_TEST..."
        
        local start_time=$(date +%s.%N)
        
        # Run the game and capture JSON output
        local game_json=$(eval "$test_command" 2>/dev/null)
        local end_time=$(date +%s.%N)
        local game_time=$(echo "$end_time - $start_time" | bc)
        
        # Parse JSON results using yq
        local our_score=$(echo "$game_json" | yq eval '.score[0]' -)
        local enemy_score=$(echo "$game_json" | yq eval '.score[1]' -)
        local our_status=$(echo "$game_json" | yq eval '.status[0]' -)
        local enemy_status=$(echo "$game_json" | yq eval '.status[1]' -)
        local turns=$(echo "$game_json" | yq eval '.game_length' -)
        
        # Determine winner based on scores and status
        local result="DRAW"
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
        
        # Extract replay data
        local replay_data=$(echo "$game_json" | yq eval '.replaydata' -)
        
        # Store game result for JSON output with replay data
        game_results+=("{\"game\": $i, \"result\": \"$result\", \"our_score\": $our_score, \"enemy_score\": $enemy_score, \"our_status\": \"$our_status\", \"enemy_status\": \"$enemy_status\", \"turns\": $turns, \"time\": $game_time, \"replaydata\": $replay_data}")
        
        echo "    Game $i: $result (Score: $our_score vs $enemy_score, Status: $our_status vs $enemy_status, ${turns} turns, ${game_time}s)"
    done
    
    # Calculate averages
    local avg_turns=$(echo "scale=2; $total_turns / $GAMES_PER_TEST" | bc)
    local avg_time=$(echo "scale=2; $total_time / $GAMES_PER_TEST" | bc)
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
        \"average_time\": $avg_time,
        \"game_results\": [$(IFS=','; echo "${game_results[*]}")]
    }"
    
    # Append to results file
    if [ -f "$results_file" ]; then
        # If file exists, add to existing array
        local temp_file=$(mktemp)
        echo "$test_json" > "$temp_file"
        yq eval '. + [load("'$temp_file'")]' "$results_file" > "${results_file}.tmp" && mv "${results_file}.tmp" "$results_file"
        rm "$temp_file"
    else
        # Create new file with array
        echo "[$test_json]" > "$results_file"
    fi
    
    echo -e "${GREEN}  Results: $wins wins, $losses losses, $draws draws (${win_rate}% win rate)${NC}"
    echo -e "  Average: ${avg_turns} turns, ${avg_time}s per game"
    echo ""
}

# Initialize results file
echo "[]" > "$STATS_FILE"

# Statistics 1: vs RandomBot
run_statistics "vs RandomBot" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns $TURNS_PER_GAME --map_file maps/maze/maze_02p_01.map 'python3 src/bots/ants.py' 'python3 src/sample_bots/python/RandomBot.py' --nolaunch --json"

# Statistics 2: vs HunterBot
run_statistics "vs HunterBot" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns $TURNS_PER_GAME --map_file maps/maze/maze_02p_01.map 'python3 src/bots/ants.py' 'python3 src/sample_bots/python/HunterBot.py' --nolaunch --json"

# Statistics 3: vs GreedyBot
run_statistics "vs GreedyBot" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns $TURNS_PER_GAME --map_file maps/maze/maze_02p_01.map 'python3 src/bots/ants.py' 'python3 src/sample_bots/python/GreedyBot.py' --nolaunch --json"

# Statistics 4: vs LeftyBot
run_statistics "vs LeftyBot" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns $TURNS_PER_GAME --map_file maps/maze/maze_02p_01.map 'python3 src/bots/ants.py' 'python3 src/sample_bots/python/LeftyBot.py' --nolaunch --json"

# Statistics 5: Four-player game
run_statistics "Four Player Game" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed \$((RANDOM % 10000)) --end_wait=0.1 --log_dir $LOG_DIR --turns $TURNS_PER_GAME --map_file maps/maze/maze_04p_01.map 'python3 src/bots/ants.py' 'python3 src/sample_bots/python/RandomBot.py' 'python3 src/sample_bots/python/HunterBot.py' 'python3 src/sample_bots/python/GreedyBot.py' --nolaunch --json"

echo -e "${BLUE}Statistics Complete${NC}"
echo "===================="
echo "Results saved to: $STATS_FILE"
echo ""

# Show summary using yq
echo -e "${GREEN}Final Summary:${NC}"
echo "=============="
yq eval '.[] | "\(.test_name): \(.wins) wins, \(.losses) losses, \(.draws) draws (\(.win_rate)% win rate)"' "$STATS_FILE"

echo ""
echo -e "${GREEN}Statistics completed!${NC}"
echo ""
echo "You can analyze the results further with yq:"
echo "  yq eval '.[] | select(.test_name == \"vs RandomBot\")' $STATS_FILE"
echo "  yq eval '.[] | {test: .test_name, win_rate: .win_rate}' $STATS_FILE"
