#!/bin/bash
# Docker-based testing script for AntsAIBot
# Provides consistent testing environment across different systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="antsaibot"
CONTAINER_NAME="antsaibot-test"
LOG_DIR="game_logs"

echo -e "${BLUE}AntsAIBot Docker Testing${NC}"
echo "========================="
echo ""

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running or not accessible${NC}"
        exit 1
    fi
}

# Function to build Docker image
build_image() {
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -t "$IMAGE_NAME" .
    echo -e "${GREEN}✓ Image built successfully${NC}"
}

# Function to run test in Docker
run_docker_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${YELLOW}Running: $test_name${NC}"
    
    # Create container and run test
    docker run --rm \
        -v "$(pwd)/$LOG_DIR:/app/$LOG_DIR" \
        -v "$(pwd)/benchmark_results:/app/benchmark_results" \
        --name "$CONTAINER_NAME" \
        "$IMAGE_NAME" \
        bash -c "$test_command"
    
    echo -e "${GREEN}✓ Test completed${NC}"
}

# Function to run interactive Docker session
run_interactive() {
    echo -e "${YELLOW}Starting interactive Docker session...${NC}"
    echo "You can run tests manually in the container."
    echo "Type 'exit' to leave the container."
    echo ""
    
    docker run -it --rm \
        -v "$(pwd):/app" \
        -w /app \
        --name "$CONTAINER_NAME" \
        "$IMAGE_NAME" \
        /bin/bash
}

# Function to clean up
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    docker container rm -f "$CONTAINER_NAME" 2>/dev/null || true
}

# Main script logic
case "${1:-help}" in
    "build")
        check_docker
        build_image
        ;;
    "test")
        check_docker
        build_image
        echo ""
        echo -e "${BLUE}Running Docker Tests${NC}"
        echo "==================="
        
        # Quick test
        run_docker_test "Quick Test" \
            "PYTHONPATH=. python3 src/tools/playgame.py --engine_seed 42 --player_seed 42 --end_wait=0.25 --verbose --log_dir $LOG_DIR --turns 30 --map_file maps/maze/maze_02p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/RandomBot.py'"
        
        # Full test
        run_docker_test "Full Test" \
            "PYTHONPATH=. python3 src/tools/playgame.py --player_seed 42 --end_wait=0.25 --verbose --log_dir $LOG_DIR --turns 1000 --map_file maps/maze/maze_04p_01.map 'python3 src/bots/bot.py' 'python3 src/sample_bots/python/RandomBot.py' 'python3 src/sample_bots/python/HunterBot.py' 'python3 src/sample_bots/python/GreedyBot.py'"
        
        echo -e "${GREEN}All Docker tests completed!${NC}"
        ;;
    "benchmark")
        check_docker
        build_image
        echo ""
        echo -e "${BLUE}Running Docker Benchmark${NC}"
        echo "========================"
        
        # Run benchmark in Docker
        run_docker_test "Benchmark Suite" \
            "chmod +x scripts/benchmark.sh && ./scripts/benchmark.sh"
        
        echo -e "${GREEN}Docker benchmark completed!${NC}"
        ;;
    "interactive")
        check_docker
        build_image
        run_interactive
        ;;
    "clean")
        cleanup
        echo -e "${GREEN}Cleanup completed${NC}"
        ;;
    "help"|*)
        echo "Usage: $0 {build|test|benchmark|interactive|clean|help}"
        echo ""
        echo "Commands:"
        echo "  build       Build the Docker image"
        echo "  test        Run basic tests in Docker"
        echo "  benchmark   Run benchmark suite in Docker"
        echo "  interactive Start interactive Docker session"
        echo "  clean       Clean up Docker containers"
        echo "  help        Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 build"
        echo "  $0 test"
        echo "  $0 benchmark"
        echo "  $0 interactive"
        ;;
esac
