#!/bin/bash

clear
figlet "HORSE P&P NDT"
figlet -f ./scripts/smkeyboard.flf "DEMO#10"
echo
echo "[HORSE SAN] Collecting the topology file from SM and storing it in the /data directory"
curl http://192.168.130.48:8000/file -o data/topology.txt
python3 ./HORSE_dashboard/update_senderv2.py box2 green "NDT Ready"
python3 HORSE_dashboard/update_senderv2.py box1 green "EM Interface Initialized"

echo "[HORSE SAN] Starting the continuous loop..."
echo

while true; do
    cd sync_and_predict/ || exit
    ./run_PT_to_NDT_v4.sh
    cd ..
    cd PcapNinja/ || exit
    ./analyze_pcap_CNIT.sh
    cd ..
done

