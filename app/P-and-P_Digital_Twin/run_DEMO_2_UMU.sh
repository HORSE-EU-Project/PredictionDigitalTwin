clear
figlet "HORSE P&P NDT"
figlet -f ./scripts/smkeyboard.flf "DEMO#2"
echo
echo "[HORSE SAN] Collecting the topology file from SM and storing it in the /data directory"
curl http://10.208.11.69:8000/file -o data/topology.txt
echo
echo "[HORSE SAN] Activating EM Interface"
cd ./HORSE_EM_interface/
./run_EM_interface.sh &

