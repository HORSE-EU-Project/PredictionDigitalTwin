#!/bin/bash

# Run the command and store the output in a variable
output=$(./cmd_container.sh ue ifconfig 2>&1 | grep uesimtun)

# Name of the Docker container to check
CONTAINER_NAME="NTFY"

# Check if the output contains at least one line
if [ -n "$output" ]; then
    echo "OK"
    if [ $(docker inspect -f '{{.State.Running}}' $CONTAINER_NAME) = "true" ]; then
        curl -d "5G emulated network OK" localhost:1236/digitaltwin
    else
        echo "The notification container is not running."
    fi
else
    echo "ERROR"
    if [ $(docker inspect -f '{{.State.Running}}' $CONTAINER_NAME) = "true" ]; then
        curl -d "5G emulated network DOWN" localhost:1236/digitaltwin
    else
        echo "The notification container is not running."
    fi
fi
