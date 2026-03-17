#!/bin/bash

# --- File Copy Script ---
# This script copies a file from a source directory to a destination directory,
# optionally renaming it in the process.

# --- Configuration Variables (Modify these values) ---

# 1. The full path to the source directory.
# Example: /home/user/documents
SOURCE_DIR="/packet-capture/cnit/demo-10/api-exposure/live"

# 2. The full path to the destination directory.
# Example: /home/user/backups
DEST_DIR="/tmp/pcap_destination"

# 3. The name of the file to be copied from the source directory.
INPUT_FILENAME="2025_11_19-13_36_25-normal.pcap"

# 4. The desired name for the file in the destination directory.
# If you want to keep the same name, set this to the same value as INPUT_FILENAME.
OUTPUT_FILENAME="current.pcap"

# --- Script Logic ---

# Full path of the source file
SOURCE_FILE="$SOURCE_DIR/$INPUT_FILENAME"

# Full path of the destination file
DEST_FILE="$DEST_DIR/$OUTPUT_FILENAME"

echo "Starting file copy process..."
echo "Source File: $SOURCE_FILE"
echo "Destination File: $DEST_FILE"

# 1. Check if the source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory '$SOURCE_DIR' not found."
    exit 1
fi

# 2. Check if the source file exists
if [ ! -f "$SOURCE_FILE" ]; then
    echo "Error: Source file '$SOURCE_FILE' not found."
    exit 1
fi

# 3. Create the destination directory if it doesn't exist (using -p for parents/no error)
mkdir -p "$DEST_DIR"

# 4. Execute the copy command
# The -v flag provides verbose output, showing the operation
if cp -v "$SOURCE_FILE" "$DEST_FILE"; then
    echo "Success: File copied and renamed successfully."
else
    echo "Error: File copy failed."
    exit 1
fi

exit 0
