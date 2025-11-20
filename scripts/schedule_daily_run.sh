#!/bin/bash

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="$PROJECT_DIR/scripts/run_daily_setup.py"
PYTHON_PATH="$PROJECT_DIR/venv/bin/python"
LOG_FILE="$PROJECT_DIR/logs/cron_job.log"

# Check if the script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: Script not found at $SCRIPT_PATH"
    exit 1
fi

# Check if python exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: Python interpreter not found at $PYTHON_PATH"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# Prepare the cron job command
# Run at 8:00 AM every day
CRON_CMD="0 8 * * * cd $PROJECT_DIR && $PYTHON_PATH $SCRIPT_PATH >> $LOG_FILE 2>&1"

# Check if the job is already in crontab
(crontab -l 2>/dev/null | grep -F "$SCRIPT_PATH") && echo "Job already scheduled." && exit 0

# Add the job to crontab
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "Successfully scheduled daily run at 8:00 AM."
echo "Command: $CRON_CMD"
