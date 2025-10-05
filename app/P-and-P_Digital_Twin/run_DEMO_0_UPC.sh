clear
figlet "HORSE P&P NDT"
figlet -f ./scripts/smkeyboard.flf "DEMO#0"
echo
echo "[HORSE SAN] Collecting the topology file from SM and storing it in the /data directory"
#curl http://10.19.2.15:8000/file -o data/topology.txt
python3 HORSE_dashboard/update_senderv2.py box2 green "NDT Ready"
sleep 5
echo 
echo "[HORSE SAN] Activating EM Interface"
cd ./HORSE_EM_interface/
./run_EM_interface_UPC.sh &
python3 HORSE_dashboard/update_senderv2.py box1 green "EM Message Received"
sleep 10
./monitor_file_UPC.sh ./last.xml
python3 HORSE_dashboard/update_senderv2.py box3 green "Message to DTE Sent"

