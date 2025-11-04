#!/bin/bash
sudo mn -c
./clean.sh log
clear 
sleep 1
figlet "HORSE P&P NDT"
figlet -f ./scripts/smkeyboard.flf "Real time prediction"
echo
echo "[HORSE SAN] Collecting the topology file from SM and storing it in the /data directory"
#curl http://10.19.2.15:8000/file -o data/topology.txt
echo "[HORSE SAN] Running P&P NDT components..."
echo
echo "[ sFlow ] *** Running sFlow"
./sflow-rt/start.sh &
sleep 5
echo "[ Monitoring] *** Launching cAdvisor, Prometheus and Grafana"
cd network_monitoring
docker compose up -d
cd ..
echo "[ NDT ] *** Running Digital Twin Engine (Comnetsemu)"
sudo python3 DT_v2.4.py
