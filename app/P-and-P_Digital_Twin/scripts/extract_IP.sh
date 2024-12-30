#!/usr/bin/env bash

# Specify the network interface name (e.g., eth0, enp0s3, wlan0)
INTERFACE="enp0s1"

# Get the IPv4 address associated with the specified interface
MY_IP=$(ip -4 -o addr show "$INTERFACE" | awk '{print $4}' | cut -d/ -f1)

# Print the IP address
echo "IP address of $INTERFACE: $MY_IP"
