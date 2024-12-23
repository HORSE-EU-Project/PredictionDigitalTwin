#!/bin/bash

# Run the command and store the output (including errors) in a variable
output=$(./cmd_container.sh ue1 ifconfig 2>&1 | grep uesimtun)

# Check if the output contains at least one line
while [ -z "$output" ]; do
    sleep 1  # Wait for 1 second before checking again
    output=$(./cmd_container.sh ue1 ifconfig 2>&1 | grep uesimtun)
done

echo "OK"
