#!/bin/bash

# Create a log file
LOG_FILE="/Users/jacques/DevFolder/elec-token-vending-original/debug_log.txt"
echo "Script started: $(date)" > "$LOG_FILE"

# Create an AppleScript to run the application in a Terminal window
osascript -e 'tell application "Terminal"
    activate
    do script "cd /Users/jacques/DevFolder/elec-token-vending-original/ && /opt/homebrew/bin/python3.12 electricity_system.py"
end tell' 2>> "$LOG_FILE"

echo "Script completed: $(date)" >> "$LOG_FILE"
