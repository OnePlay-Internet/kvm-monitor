#!/bin/bash

# Name of the process to check (without path)
PROCESS_NAME="system_monitor.py"

# Directory of your Python virtual environment
VENV_DIR="/path/to/your/venv"

# Directory where your Python script is located
SCRIPT_DIR="/path/to/your/script"

# Name of your Python script
SCRIPT_NAME="your_script.py"

# Check if the process is running
if ! pgrep -f "$PROCESS_NAME" > /dev/null
then
    echo "Process $PROCESS_NAME is not running. Starting it..."

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Change directory to the script location
    cd "$SCRIPT_DIR"

    # Launch the Python script
    nohup python "$SCRIPT_NAME" &

    echo "Process $PROCESS_NAME started."
else
    echo "Process $PROCESS_NAME is already running."
fi
