#!/bin/bash

# Check if eth1 exists
if ip link show eth1 &>/dev/null; then
    INTF="eth1"
else
    INTF="enp0s1"
fi

echo "INTF is set to: $INTF"
