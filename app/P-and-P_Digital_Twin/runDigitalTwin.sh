#!/bin/bash

./clean.sh log
clear 
sleep 1
echo "[ sFlow ] *** Running sFlow"
./sflow-rt/start.sh &
sleep 5
echo "[ Monitoring] *** Launching cAdvisor, Prometheus and Grafana"
cd network_monitoring
docker compose up -d
cd ..
echo "[ NDT ] *** Running Digital Twin Engine (Comnetsemu)"
sudo python3 DT_v2.3.py
