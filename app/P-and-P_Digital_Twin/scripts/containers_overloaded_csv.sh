#!/bin/bash

# Set the threshold values (adjust as needed)
CPU_THRESHOLD=80  # Percentage (e.g., 80%)
MEMORY_THRESHOLD=512  # MB (e.g., 512 MB)

# Output file with prefix and timestamp
OUTPUT_PREFIX="../data/docker_usage"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="${OUTPUT_PREFIX}_${TIMESTAMP}.csv"

# Get container IDs
CONTAINER_IDS=$(docker ps -q)

# Initialize the output file
echo "Container Name, CPU Usage (%), Memory Usage (MB)" > "$OUTPUT_FILE"

# Initialize a flag to track if any container exceeds thresholds
CONTAINER_EXCEEDED=false

# Loop through each container
for CONTAINER_ID in $CONTAINER_IDS; do
    # Get container stats (CPU and memory)
    STATS=$(docker stats --no-stream "$CONTAINER_ID" --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}}")

    # Extract CPU and memory values
    CPU_USAGE=$(echo "$STATS" | awk -F, '{print $2}' | sed 's/%//')
    MEMORY_USAGE=$(echo "$STATS" | awk -F, '{print $3}' | sed 's/[^0-9]//g')

    # Check if CPU or memory exceeds thresholds
    if (( $(echo "$CPU_USAGE > $CPU_THRESHOLD" | bc -l) )) || (( MEMORY_USAGE > MEMORY_THRESHOLD )); then
        echo "$STATS" >> "$OUTPUT_FILE"
        CONTAINER_EXCEEDED=true
    fi
done

# Check if any data was written to the file
if [ "$CONTAINER_EXCEEDED" = true ]; then
    echo "Container usage data written to $OUTPUT_FILE"
else
    echo "No container exceeded the thresholds."
    rm "$OUTPUT_FILE"  # Remove the empty file
fi
