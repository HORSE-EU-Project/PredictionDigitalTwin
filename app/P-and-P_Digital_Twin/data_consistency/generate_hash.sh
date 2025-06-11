#!/bin/bash

# This script generates a SHA256 hash of a specified file
# and saves it to a new file with a .hash extension.

# Check if a file path is provided as an argument
if [ -z "$1" ]; then
    echo "Usage: $0 <file_path>"
    echo "Example: $0 mydocument.txt"
    exit 1
fi

FILE_PATH="$1"

# Check if the file exists
if [ ! -f "$FILE_PATH" ]; then
    echo "Error: File '$FILE_PATH' not found."
    exit 1
fi

HASH_FILE_PATH="${FILE_PATH}.hash"

echo "Generating SHA256 hash for: $FILE_PATH"

# Calculate the SHA256 hash and extract only the hash value (first field)
# Then save it to the .hash file
sha256sum "$FILE_PATH" | awk '{print $1}' > "$HASH_FILE_PATH"

if [ $? -eq 0 ]; then
    echo "Hash successfully generated and saved to: $HASH_FILE_PATH"
else
    echo "Error: Failed to generate hash for $FILE_PATH."
    exit 1
fi

exit 0
