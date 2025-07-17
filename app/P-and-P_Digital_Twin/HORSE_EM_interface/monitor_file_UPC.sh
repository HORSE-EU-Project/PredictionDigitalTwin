#!/bin/bash

# This script monitors a specified file for changes in its modification timestamp.
# It checks every 30 seconds and prints a message if the file has been updated.

# Check if a file path is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <file_path>"
  echo "Example: $0 /path/to/your/file.txt"
  exit 1
fi

FILE_TO_MONITOR="$1"
SLEEP_INTERVAL=30 # seconds

# Check if the file exists
if [ ! -f "$FILE_TO_MONITOR" ]; then
  echo "Error: File '$FILE_TO_MONITOR' not found."
  exit 1
fi

echo "Monitoring file: '$FILE_TO_MONITOR' for updates every ${SLEEP_INTERVAL} seconds."

# Get the initial modification timestamp of the file
# Using stat -c %Y gives the last modification time in seconds since the Epoch
LAST_MOD_TIMESTAMP=$(stat -c %Y "$FILE_TO_MONITOR")

echo "Initial timestamp: $(date -d @"$LAST_MOD_TIMESTAMP")"

# Loop forever to check for updates
while true; do
  # Get the current modification timestamp
  CURRENT_MOD_TIMESTAMP=$(stat -c %Y "$FILE_TO_MONITOR")

  # Compare current timestamp with the last known timestamp
  if [ "$CURRENT_MOD_TIMESTAMP" -ne "$LAST_MOD_TIMESTAMP" ]; then
    echo "File updated! (Previous: $(date -d @"$LAST_MOD_TIMESTAMP"), Current: $(date -d @"$CURRENT_MOD_TIMESTAMP"))"
    LAST_MOD_TIMESTAMP="$CURRENT_MOD_TIMESTAMP" # Update the stored timestamp
    cd ../HORSE_DTE_interface/
    echo "[HORSE SAN] Contacting DTE"
    echo "[HORSE DTE] Answer:"
    ./test_DTE_UPC.sh
    cd ../HORSE_EM_interface/
  fi

  # Wait for the specified interval before checking again
  sleep "$SLEEP_INTERVAL"
done
