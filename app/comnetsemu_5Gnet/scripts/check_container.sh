#!/bin/bash

# Name of the Docker container to check
CONTAINER_NAME="NTFY"

# Check if the Docker container is running
if [ $(docker inspect -f '{{.State.Running}}' $CONTAINER_NAME) = "true" ]; then
  echo "Success: Container is running."
else
  echo "The container is not running."
fi
