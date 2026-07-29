#!/bin/bash

# Stop Tuya GUI server running on port 5001 (inside homeassistant Docker container)

echo "Stopping Tuya GUI on port 5001 (inside homeassistant container)..."

# Find and kill the tuya_gui.py process specifically
echo "Finding tuya_gui.py processes inside homeassistant container..."
PYTHON_PIDS=$(docker exec homeassistant pgrep -f "tuya_gui.py" 2>/dev/null)

if [ -z "$PYTHON_PIDS" ]; then
    echo "No tuya_gui.py process found"
else
    echo "Found tuya_gui.py processes: $PYTHON_PIDS"
    docker exec homeassistant kill -9 $PYTHON_PIDS
    echo "tuya_gui.py processes killed successfully"
fi

echo "Done."