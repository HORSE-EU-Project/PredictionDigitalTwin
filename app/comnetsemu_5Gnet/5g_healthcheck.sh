#!/bin/bash

# Run the command and store the output in a variable
output=$(./cmd_container.sh ue ifconfig 2>&1 | grep uesimtun)

# Check if the output contains at least one line
if [ -n "$output" ]; then
    echo "OK"
else
    echo "ERROR"
fi
