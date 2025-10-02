#!/bin/bash
# full test suite for AntsAIBot
# Runs multiple test scenarios and generates a report

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_DIR="game_logs"
REPORT_FILE="test_report.txt"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

echo -e "${BLUE}AntsAIBot Test Suite${NC}"
echo "====================="
echo "Timestamp: $TIMESTAMP"
echo ""

# Initialize report
echo "AntsAIBot Test Report - $TIMESTAMP" > "$REPORT_FILE"
echo "=================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Function to run a test and capture results
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_duration="$3"
    
    echo -e "${YELLOW}Running: $test_name${NC}"
    echo "Test: $test_name" >> "$REPORT_FILE"
    echo "Command: $test_command" >> "$REPORT_FILE"
    
    local start_time=$(date +%s)
    
    if eval "$test_command" >> "$REPORT_FILE" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${GREEN}✓ PASSED${NC} (${duration}s)"
        echo "Result: PASSED (${duration}s)" >> "$REPORT_FILE"
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${RED}✗ FAILED${NC} (${duration}s)"
        echo "Result: FAILED (${duration}s)" >> "$REPORT_FILE"
    fi
    
    echo "" >> "$REPORT_FILE"
    echo ""
}

# Test 1: Quick functionality test
run_test "Quick Test (30 turns)" \
    "PYTHONPATH=. python3 src/tools/playgame.py --engine_seed 42 --player_seed 42 --end_wait=0.25 --verbose --log_dir $LOG_DIR --turns 30 --map_file maps/maze/maze_02p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/RandomBot.py' --nolaunch" \
    10

# Test 2: Bot against RandomBot
run_test "vs RandomBot (1000 turns)" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed 42 --end_wait=0.25 --verbose --log_dir $LOG_DIR --turns 1000 --map_file maps/maze/maze_02p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/RandomBot.py' --nolaunch" \
    30

# Test 3: Bot against HunterBot
run_test "vs HunterBot (1000 turns)" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed 42 --end_wait=0.25 --verbose --log_dir $LOG_DIR --turns 1000 --map_file maps/maze/maze_02p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/HunterBot.py' --nolaunch" \
    30

# Test 4: Bot against GreedyBot
run_test "vs GreedyBot (1000 turns)" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed 42 --end_wait=0.25 --verbose --log_dir $LOG_DIR --turns 1000 --map_file maps/maze/maze_02p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/GreedyBot.py' --nolaunch" \
    30

# Test 5: Bot against LeftyBot
run_test "vs LeftyBot (1000 turns)" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed 42 --end_wait=0.25 --verbose --log_dir $LOG_DIR --turns 1000 --map_file maps/maze/maze_02p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/LeftyBot.py' --nolaunch" \
    30

# Test 6: Four-player game
run_test "Four-Player Game (1000 turns)" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed 42 --end_wait=0.25 --verbose --log_dir $LOG_DIR --turns 1000 --map_file maps/maze/maze_04p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/RandomBot.py' 'python3 src/sample_bots/python/HunterBot.py' 'python3 src/sample_bots/python/GreedyBot.py' --nolaunch" \
    45

# Test 7: Self-play test
run_test "Self-Play Test (1000 turns)" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed 42 --end_wait=0.25 --verbose --log_dir $LOG_DIR --turns 1000 --map_file maps/maze/maze_04p_01.map 'python3 src/bots/bot.py' 'python3 src/bots/bot.py' 'python3 src/bots/bot.py' 'python3 src/bots/bot.py' --nolaunch" \
    45

# Test 8: Different map test
run_test "Different Map Test (500 turns)" \
    "PYTHONPATH=. python3 src/tools/playgame.py --player_seed 42 --end_wait=0.25 --verbose --log_dir $LOG_DIR --turns 500 --map_file maps/maze/maze_02p_02.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/RandomBot.py' --nolaunch" \
    20

echo -e "${BLUE}Test Suite Complete${NC}"
echo "===================="
echo "Report saved to: $REPORT_FILE"
echo "Game logs saved to: $LOG_DIR/"
echo ""

# Count replay files
REPLAY_COUNT=$(ls -1 "$LOG_DIR"/*.replay 2>/dev/null | wc -l)
echo "Generated $REPLAY_COUNT replay files"

# Show latest replay
LATEST_REPLAY=$(ls -t "$LOG_DIR"/*.replay 2>/dev/null | head -1)
if [ -n "$LATEST_REPLAY" ]; then
    echo "Latest replay: $LATEST_REPLAY"
    echo "To visualize: python3 visualizer/visualize_locally.py '$LATEST_REPLAY'"
fi

echo ""
echo -e "${GREEN}All tests completed!${NC}"
