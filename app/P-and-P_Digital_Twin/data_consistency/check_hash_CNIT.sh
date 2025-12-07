#!/bin/bash

# This script checks the consistency of a file's content
# against its stored SHA256 hash in a .hash file.

# Check if a file path is provided as an argument
if [ -z "$1" ]; then
    echo "Usage: $0 <file_path>"
    echo "Example: $0 mydocument.txt"
    exit 1
fi

FILE_PATH="$1"
HASH_FILE_PATH="${FILE_PATH}.hash"

# Check if the original file exists
if [ ! -f "$FILE_PATH" ]; then
    echo "Error: Original file '$FILE_PATH' not found."
    exit 1
fi

# Check if the hash file exists
if [ ! -f "$HASH_FILE_PATH" ]; then
    echo "Error: Hash file '$HASH_FILE_PATH' not found. Please generate it first."
    exit 1
fi

echo "[HORSE SAN] Checking consistency for: $FILE_PATH"
sleep 5

# Calculate the current SHA256 hash of the file
CURRENT_HASH=$(sha256sum "$FILE_PATH" | awk '{print $1}')

# Read the stored hash from the .hash file
STORED_HASH=$(cat "$HASH_FILE_PATH")

# Compare the hashes
if [ "$CURRENT_HASH" = "$STORED_HASH" ]; then
    echo "Status: SUCCESS - The file '$FILE_PATH' is consistent with its hash."
    python3 ../HORSE_dashboard/update_senderv2.py box2 green "P&P NDT data ok"
    echo
    echo "[HORSE SAN] Continuing the prediction process..."
    sleep 20
else
    echo "Status: FAILED - The file '$FILE_PATH' has been modified or is inconsistent!"
    echo "  Current Hash: $CURRENT_HASH"
    echo "  Stored Hash:  $STORED_HASH"
    python3 ../HORSE_dashboard/update_senderv2.py box2 red "P&P NDT data corrupt"
    echo
    echo "[HORSE SAN] Contacting DTE"
    echo -e "[ \n  {\n    "prediction": "data_poisoning",\n    "confidence": 1.0\n  }\n]"
    echo "[HORSE DTE] Answer:"
    ./test_DTE_CNIT.sh
    python3 ../HORSE_dashboard/update_senderv2.py box3 green "DTE Message Sent"
    echo
    echo "[HORSE SAN] SYSTEM RESTART RECOMMENDED - exiting"
    sleep 10
    echo
    echo "[HORSE SAN] P&P NDT stopped"
fi

exit 0
