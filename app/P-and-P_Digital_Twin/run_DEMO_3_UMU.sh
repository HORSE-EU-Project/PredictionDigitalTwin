clear
figlet "HORSE P&P NDT"
figlet -f ./scripts/smkeyboard.flf "DEMO#3"
echo
echo "[HORSE SAN] Collecting the topology file from SM and storing it in the /data directory"
curl http://10.208.11.69:8000/file -o data/topology.txt 
python3 HORSE_dashboard/update_senderv2.py box2 green "NDT Initialized"
python3 HORSE_dashboard/update_senderv2.py box1 green "EM Interface Initialized"
echo
echo "[HORSE SAN] Activating EM Interface"
cd ./HORSE_EM_interface/
./run_EM_interface_3_UMU.sh &

