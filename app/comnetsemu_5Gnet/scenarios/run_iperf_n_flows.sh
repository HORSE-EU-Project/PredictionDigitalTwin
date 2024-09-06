#!/bin/bash

# Generate a random number between 1 and 10
#../cmd_container.sh ue "random_number=$((RANDOM % 10 + 1)); echo $random_number"
#../cmd_container.sh ue bandwidth="${random_number}M"

# Generate data flows
../cmd_container.sh ue "iperf3 -t 60 -b 4m -c 192.168.0.201" &
