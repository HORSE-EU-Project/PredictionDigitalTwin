#!/bin/bash

# This script prints the current timestamp and its own Process ID (PID).

# Get the current timestamp
# The '+%Y-%m-%d %H:%M:%S' format ensures a readable date and time.
TIMESTAMP=$(date +%Y-%m-%d\ %H:%M:%S)

# Get the current process ID
# '$$' is a special shell variable that holds the PID of the current script.
PID=$$

# Print the timestamp and PID
echo "Timestamp: $TIMESTAMP, PID: $PID"
