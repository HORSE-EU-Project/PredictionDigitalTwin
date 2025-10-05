clear
figlet "HORSE P&P NDT"
figlet -f ./scripts/smkeyboard.flf "DEMO#4"
sleep 5
echo
echo "[HORSE SAN] Collecting topology file from SM"
curl http://10.208.11.69:8000/file -o data/topology.txt
sleep 5
echo
echo "[HORSE SAN] Running data consistency check" 
cd data_consistency
./check_hash_UMU.sh input.pcap
