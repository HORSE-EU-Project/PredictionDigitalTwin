#!/bin/bash

# This script runs iperf3 inside a container.
# The container name is the first argument ($1).
# The binding IP address (-B) is the second argument ($2).
# The client IP address (-c) is the third argument ($3).

../cmd_container.sh "$1" "iperf3 -B $2 -c $3"
