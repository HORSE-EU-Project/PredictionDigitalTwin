#!/bin/bash
#
# Script: move_latest_pcap.sh
# Description: Identifies the most recently modified .pcap file in a source
# directory and copies it to a destination directory with a specified filename.

# ===============================================
# 1. Configuration Variables (Internal)
# ===============================================

# Directory where the .pcap files are located.
SOURCE_DIR="/packet-capture/cnit/demo-10/api-exposure/2025_11_19"

# Directory where the most recent file should be copied.
DEST_DIR="/tmp/pcap_destination"

# The desired name of the copied output file.
OUTPUT_FILENAME="latest_capture_$(date +%Y%m%d_%H%M%S).pcap"

# Full path for the destination file
DEST_FILE="${DEST_DIR}/${OUTPUT_FILENAME}"

# ===============================================
# 2. Setup and Validation
# ===============================================

echo "Starting PCAP file transfer utility..."

# Check if the source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory not found: $SOURCE_DIR" >&2
    exit 1
fi

# Check if the destination directory exists (create it if it doesn't)
if [ ! -d "$DEST_DIR" ]; then
    echo "Destination directory not found. Creating $DEST_DIR..."
    mkdir -p "$DEST_DIR"
    if [ $? -ne 0 ]; then
        echo "Error: Could not create destination directory: $DEST_DIR" >&2
        exit 1
    fi
fi

# ===============================================
# 3. Find the Most Recent File
# ===============================================

echo "Searching for the most recent .pcap file in $SOURCE_DIR..."

# Use 'find' to get a list of .pcap files, sort them by modification time (t),
# reverse the order (r) to put the newest last, and take the last line (tail -n 1).
# We use find for robustness, but then filter through ls for the simplest approach.
# A simpler, common approach using ls -t:
LATEST_PCAP=$(ls -t "$SOURCE_DIR"/*.pcap 2>/dev/null | head -n 1)

# Check if any file was found (the variable will be non-empty)
if [ -z "$LATEST_PCAP" ]; then
    echo "No .pcap files found in $SOURCE_DIR." >&2
    exit 1
fi

# ===============================================
# 4. Copy the File
# ===============================================

echo "Found latest PCAP file: ${LATEST_PCAP}"
echo "Copying to: ${DEST_FILE}"

# Use 'cp' to copy the file. Using -v for verbose output.
cp -v "${LATEST_PCAP}" "${DEST_FILE}"

if [ $? -eq 0 ]; then
    echo "Success! File copied and renamed."
    echo "Source: ${LATEST_PCAP}"
    echo "Destination: ${DEST_FILE}"
else
    echo "Error: Failed to copy the file." >&2
    exit 1
fi

# Clean exit
exit 0
