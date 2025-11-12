clear
figlet "HORSE P&P NDT"
figlet -f ./scripts/smkeyboard.flf "DEMO#10"
echo
echo "[HORSE SAN] Collecting the topology file from SM and storing it in the /data directory"
curl http://192.168.130.48:8000/file -o data/topology.txt
python3 ./HORSE_dashboard/update_senderv2.py box2 green "NDT Ready"
sleep 5
echo 
echo "[HORSE SAN] Activating EM Interface"
cd ./HORSE_EM_interface/
./run_EM_interface_CNIT.sh &
python3 ../HORSE_dashboard/update_senderv2.py box1 green "EM Message Received"
sleep 10
python3 ../HORSE_dashboard/update_senderv2.py box3 green "DTE Interface Ready" 
./monitor_file_CNIT.sh ./last.xml

