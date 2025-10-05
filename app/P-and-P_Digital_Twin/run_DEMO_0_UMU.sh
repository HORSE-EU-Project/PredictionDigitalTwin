clear
figlet "HORSE P&P NDT"
figlet -f ./scripts/smkeyboard.flf "DEMO#0"
echo
echo "[HORSE SAN] Collecting the topology file from SM and storing it in the /data directory"
curl http://10.208.11.69:8000/file -o data/topology.txt
python3 HORSE_dashboard/update_senderv2.py box2 green "NDT Ready"
python3 HORSE_dashboard/update_senderv2.py box1 yellow "EM Interface Initialized"
sleep 5
echo
echo "[HORSE] Activating EM Interface"
cd ./HORSE_EM_interface/
./run_EM_interface.sh &
sleep 10
python3 ../HORSE_dashboard/update_senderv2.py box3 green "DTE Message Sent"
./monitor_file_UMU.sh ./last.xml
