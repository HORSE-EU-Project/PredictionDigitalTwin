#!/bin/bash

# Get the current timestamp
TIMESTAMP=$(date +"%Y%m%d%H%M%S")

# Create a CSV file with the timestamp in the filename
OUTPUT_FILE="../data/container_stats_${TIMESTAMP}.csv"

# Collect resource utilization and container names
docker stats --no-stream --format "table {{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}}" $(docker ps -q) > "$OUTPUT_FILE"

echo "Resource utilization and container names saved in $OUTPUT_FILE"
