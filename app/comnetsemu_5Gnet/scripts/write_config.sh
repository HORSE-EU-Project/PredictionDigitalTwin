#!/bin/bash

# Check if eth1 exists
if ip link show eth1 &>/dev/null; then
    INTF="eth1"
else
    INTF="enp0s1"
fi

echo "INTF is set to: $INTF"

# Get the IP address of the eth0 interface
IP_ADDRESS=$(ip addr show $INTF | grep "inet\b" | awk '{print $2}' | cut -d/ -f1)

# Write the output to a text file
echo -e "[MININET_SERVER]\nipaddr = $IP_ADDRESS\nport = 8000" > config.ini

echo "IP address extracted and written to config.ini"
