#!/bin/bash

# --- Configuration Variables ---
PREFIX="open5gs" # Default prefix, can be overridden
OUTDIR="./captures-buffer" # Default output directory, can be overridden
OUTNAME="latest_capture" # Default output name, can be overridden
PACKET_CAPTURE_DIR="/packet-capture" # Directory where pcap files are located

# --- Script Logic ---

# Function to display usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "This script finds the most recent .pcap file with a given prefix in /packet-capture"
    echo "and copies it to a specified output directory with a new name and timestamp."
    echo ""
    echo "Options:"
    echo "  -p <prefix>   Specify the prefix for the pcap file (default: $PREFIX)"
    echo "  -o <outdir>   Specify the output directory (default: $OUTDIR)"
    echo "  -n <outname>  Specify the base name for the output file (default: $OUTNAME)"
    echo "  -h            Display this help message"
    echo ""
    echo "Example: $0 -p 'my_capture' -o '/home/user/dumps' -n 'network_log'"
    exit 1
}

# Parse command-line options
while getopts "p:o:n:h" opt; do
    case ${opt} in
        p )
            PREFIX=$OPTARG
            ;;
        o )
            OUTDIR=$OPTARG
            ;;
        n )
            OUTNAME=$OPTARG
            ;;
        h )
            usage
            ;;
        \? )
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
    esac
done

# Check if the packet capture directory exists
if [ ! -d "$PACKET_CAPTURE_DIR" ]; then
    echo "Error: Packet capture directory '$PACKET_CAPTURE_DIR' not found."
    echo "Please ensure the directory exists or modify PACKET_CAPTURE_DIR in the script."
    exit 1
fi

# Create the output directory if it doesn't exist
mkdir -p "$OUTDIR"

# Find the most recent pcap file with the specified prefix
# ls -t: sorts by modification time, newest first
# grep: filters for files starting with the prefix and ending with .pcap
# head -n 1: takes only the first (most recent) result
# awk: extracts the filename
MOST_RECENT_PCAP=$(ls -t "$PACKET_CAPTURE_DIR" | grep "^$PREFIX.*\.pcap$" | head -n 1)

# Check if a file was found
if [ -z "$MOST_RECENT_PCAP" ]; then
    echo "No .pcap file with prefix '$PREFIX' found in '$PACKET_CAPTURE_DIR'."
    exit 0
fi

SOURCE_FILE="$PACKET_CAPTURE_DIR/$MOST_RECENT_PCAP"

# Get the current system timestamp
# Using date +%s for Unix timestamp (seconds since epoch) for simplicity and uniqueness
TIMESTAMP=$(date +"%Y%m%d%H%M%S")

# Construct the destination filename
DEST_FILE="${OUTDIR}/${OUTNAME}_${TIMESTAMP}.pcap"

echo "Found most recent pcap: '$SOURCE_FILE'"
echo "Copying to: '$DEST_FILE'"

# Copy the file
if cp "$SOURCE_FILE" "$DEST_FILE"; then
    echo "Successfully copied '$SOURCE_FILE' to '$DEST_FILE'."
else
    echo "Error: Failed to copy '$SOURCE_FILE' to '$DEST_FILE'."
    exit 1
fi

exit 0
