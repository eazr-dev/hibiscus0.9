#!/bin/bash

# =============================================================================
# RALPH - Autonomous AI Coding Loop for EAZR Chat
# =============================================================================
# Ships features while you sleep by running repeated iterations of an AI agent
# through a bash loop until all development tasks are complete.
#
# Usage:
#   ./scripts/ralph/ralph.sh [max_iterations]
#
# Examples:
#   ./scripts/ralph/ralph.sh        # Default: 25 iterations
#   ./scripts/ralph/ralph.sh 50     # Run up to 50 iterations
#   ./scripts/ralph/ralph.sh 10     # Run up to 10 iterations
#
# Requirements:
#   - Claude Code CLI installed: npm install -g @anthropic-ai/claude-code
#   - Or Amp installed
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MAX_ITERATIONS=${1:-25}
AGENT="claude"  # Options: "claude" or "amp"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Files
PRD_FILE="$SCRIPT_DIR/prd.json"
PROMPT_FILE="$SCRIPT_DIR/prompt.md"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"

echo -e "${CYAN}"
echo "============================================================================="
echo "  RALPH - Autonomous AI Coding Loop"
echo "  Project: EAZR Chat"
echo "============================================================================="
echo -e "${NC}"

# Verify files exist
if [ ! -f "$PRD_FILE" ]; then
    echo -e "${RED}Error: prd.json not found at $PRD_FILE${NC}"
    echo "Please create the PRD file with user stories first."
    exit 1
fi

if [ ! -f "$PROMPT_FILE" ]; then
    echo -e "${RED}Error: prompt.md not found at $PROMPT_FILE${NC}"
    echo "Please create the prompt file with instructions first."
    exit 1
fi

# Initialize progress file if it doesn't exist
if [ ! -f "$PROGRESS_FILE" ]; then
    echo "# Ralph Progress Log" > "$PROGRESS_FILE"
    echo "Initialized: $(date)" >> "$PROGRESS_FILE"
    echo "" >> "$PROGRESS_FILE"
fi

# Change to project root
cd "$PROJECT_ROOT"

# Check for required tools
check_agent() {
    if [ "$AGENT" = "claude" ]; then
        if ! command -v claude &> /dev/null; then
            echo -e "${RED}Error: Claude Code CLI not found${NC}"
            echo "Install with: npm install -g @anthropic-ai/claude-code"
            exit 1
        fi
        echo -e "${GREEN}Using Claude Code CLI${NC}"
    elif [ "$AGENT" = "amp" ]; then
        if ! command -v amp &> /dev/null; then
            echo -e "${RED}Error: Amp CLI not found${NC}"
            exit 1
        fi
        echo -e "${GREEN}Using Amp CLI${NC}"
    else
        echo -e "${RED}Error: Unknown agent '$AGENT'${NC}"
        exit 1
    fi
}

# Count remaining tasks
count_remaining_tasks() {
    if command -v jq &> /dev/null; then
        jq '[.userStories[] | select(.passes == false)] | length' "$PRD_FILE"
    else
        # Fallback: count "passes": false occurrences
        grep -c '"passes": false' "$PRD_FILE" || echo "0"
    fi
}

# Display current status
show_status() {
    echo -e "\n${BLUE}Current Status:${NC}"
    if command -v jq &> /dev/null; then
        echo -e "${YELLOW}Pending Tasks:${NC}"
        jq -r '.userStories[] | select(.passes == false) | "  [\(.id)] \(.title) (Priority: \(.priority))"' "$PRD_FILE"
        echo -e "\n${GREEN}Completed Tasks:${NC}"
        jq -r '.userStories[] | select(.passes == true) | "  [\(.id)] \(.title)"' "$PRD_FILE"
    else
        echo "Install jq for detailed status: brew install jq"
        echo "Remaining tasks: $(count_remaining_tasks)"
    fi
    echo ""
}

# Run agent with prompt
run_agent() {
    local iteration=$1

    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Iteration $iteration of $MAX_ITERATIONS${NC}"
    echo -e "${CYAN}  Started: $(date)${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}\n"

    # Read the prompt
    PROMPT=$(cat "$PROMPT_FILE")

    # Run the appropriate agent
    if [ "$AGENT" = "claude" ]; then
        # Claude Code with dangerous permissions for autonomous operation
        echo "$PROMPT" | claude --dangerously-skip-permissions
    elif [ "$AGENT" = "amp" ]; then
        # Amp with all permissions
        echo "$PROMPT" | amp --dangerously-allow-all
    fi

    # Log iteration completion
    echo "" >> "$PROGRESS_FILE"
    echo "--- Iteration $iteration completed at $(date) ---" >> "$PROGRESS_FILE"
}

# Main loop
main() {
    check_agent

    echo -e "${YELLOW}Max Iterations: $MAX_ITERATIONS${NC}"
    echo -e "${YELLOW}PRD File: $PRD_FILE${NC}"
    echo -e "${YELLOW}Progress File: $PROGRESS_FILE${NC}"

    show_status

    REMAINING=$(count_remaining_tasks)

    if [ "$REMAINING" -eq 0 ]; then
        echo -e "${GREEN}All tasks are already complete!${NC}"
        exit 0
    fi

    echo -e "${YELLOW}Starting autonomous loop with $REMAINING remaining tasks...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop at any time.${NC}"
    sleep 3

    for ((i=1; i<=MAX_ITERATIONS; i++)); do
        # Check if all tasks are complete
        REMAINING=$(count_remaining_tasks)

        if [ "$REMAINING" -eq 0 ]; then
            echo -e "\n${GREEN}════════════════════════════════════════════════════════════════════════════${NC}"
            echo -e "${GREEN}  ALL TASKS COMPLETE!${NC}"
            echo -e "${GREEN}  Finished in $((i-1)) iterations${NC}"
            echo -e "${GREEN}════════════════════════════════════════════════════════════════════════════${NC}"

            # Final status
            show_status

            # Log completion
            echo "" >> "$PROGRESS_FILE"
            echo "=== ALL TASKS COMPLETED ===" >> "$PROGRESS_FILE"
            echo "Finished at: $(date)" >> "$PROGRESS_FILE"
            echo "Total iterations: $((i-1))" >> "$PROGRESS_FILE"

            exit 0
        fi

        echo -e "${YELLOW}Tasks remaining: $REMAINING${NC}"

        # Run the agent
        run_agent $i

        # Small delay between iterations to allow for rate limiting
        if [ $i -lt $MAX_ITERATIONS ]; then
            echo -e "\n${BLUE}Waiting 5 seconds before next iteration...${NC}"
            sleep 5
        fi
    done

    # Max iterations reached
    echo -e "\n${YELLOW}════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}  Max iterations ($MAX_ITERATIONS) reached${NC}"
    echo -e "${YELLOW}  Tasks remaining: $(count_remaining_tasks)${NC}"
    echo -e "${YELLOW}════════════════════════════════════════════════════════════════════════════${NC}"

    show_status
}

# Handle interrupts gracefully
trap 'echo -e "\n${RED}Interrupted by user. Exiting...${NC}"; exit 130' INT TERM

# Run main
main
