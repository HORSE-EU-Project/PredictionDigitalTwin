#!/bin/bash

# --- Configuration Variables ---
OUTDIR="./captures-buffer" # Default output directory, can be overridden
OUTNAME="merged" # Default output name, can be overridden
PACKET_CAPTURE_DIR="/packet-capture" # Directory where pcap files are located

SOURCE_FILE_UE="$PACKET_CAPTURE_DIR/ueransim*.pcap"
SOURCE_FILE_CORE="$PACKET_CAPTURE_DIR/open5gs*.pcap"

# Get the current system timestamp
# Using date +%s for Unix timestamp (seconds since epoch) for simplicity and uniqueness
TIMESTAMP=$(date +"%Y%m%d%H%M%S")

# Construct the destination filename
DEST_FILE="${OUTDIR}/${OUTNAME}_${TIMESTAMP}.pcap"

mergecap -w "$DEST_FILE" "$PACKET_CAPTURE_DIR"/ueransim*.pcap "$PACKET_CAPTURE_DIR"/open5gs*.pcap

cd ./PcapNinja
python3 pcapninja.py --pcap_file ."$DEST_FILE"
cd ..
