clear
figlet "HORSE P&P NDT"
figlet -f ./scripts/smkeyboard.flf "DEMO#4"
sleep 5
echo
echo "[HORSE SAN] Collecting topology file from SM"
curl http://192.168.130.48:8000/file -o data/topology.txt
python3 ./HORSE_dashboard/update_senderv2.py box2 green "NDT Ready"
sleep 5
echo
echo "[HORSE SAN] Interface with EM ready"
python3 ./HORSE_dashboard/update_senderv2.py box1 green "EM Interface Ready"
echo
echo "[HORSE SAN] Running data consistency check"
python3 ./HORSE_dashboard/update_senderv2.py box2 yellow "NDT Data Verification" 
echo
cd data_consistency
./check_hash_CNIT.sh input.pcap
