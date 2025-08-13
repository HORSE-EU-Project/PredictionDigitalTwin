#!/bin/bash

# This script runs iperf3 in server mode inside a container.
# The container name is the first argument ($1).
# The binding IP address (-B) is the second argument ($2).

../cmd_container.sh "$1" "timeout 60s iperf3 -s -B $2 -p 5201"
