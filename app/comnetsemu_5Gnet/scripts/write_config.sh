#!/bin/bash

# Get the IP address of the eth0 interface
IP_ADDRESS=$(ip addr show enp0s1 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1)

# Write the output to a text file
echo -e "[MININET_SERVER]\nipaddr = $IP_ADDRESS\nport = 8000" > config.ini

echo "IP address extracted and written to config.ini"
