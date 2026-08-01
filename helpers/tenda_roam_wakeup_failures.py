#!/usr/bin/env python3
"""
Script to count Tenda Roam wake-up failures from Home Assistant log.
Outputs JSON for command_line sensor.
"""
import json
import os
import re

LOG_FILE = "/config/home-assistant.log"
SEARCH_PATTERN = "Wake-up failed for 192.168.0.25"

def main():
    count = 0
    last_message = ""
    
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()
            
            # Count occurrences and find last message
            for line in lines:
                if SEARCH_PATTERN in line:
                    count += 1
                    last_message = line.strip()
        except Exception as e:
            # If we can't read the log, return empty
            pass
    
    # Escape the last message for JSON (json.dumps handles this)
    output = {
        "count": count,
        "last_message": last_message
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()