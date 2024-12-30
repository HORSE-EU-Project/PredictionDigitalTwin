#!/bin/bash

./clean.sh log
clear 
sleep 1
echo "[ sFlow ] *** Running sFlow"
./sflow-rt/start.sh &
sleep 5
echo "[ NDT ] *** Running Digital Twin Engine (Comnetsemu)"
sudo python3 DT_v2.0.py
