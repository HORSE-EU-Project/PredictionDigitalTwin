clear
figlet "HORSE P&P NDT"
figlet -f ./scripts/smkeyboard.flf "DEMO#4"
sleep 5
echo
echo "[HORSE SAN] Collecting topology file from SM"
curl http://10.19.2.15:8000/file -o data/topology.txt
sleep 5
echo
echo "[HORSE SAN] Running data consistency check" 
cd data_consistency
./check_hash_UPC.sh input.pcap
