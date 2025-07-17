echo "[HORSE SAN] Collecting the topology file and storing it in the /data directory"
curl http://10.19.2.15:8000/file -o data/topology.txt
echo "[HORSE SAN] Activating EM Interface"
cd ./HORSE_EM_interface/
./run_EM_interface.sh &
sleep 10
./monitor_file_UPC.sh ./last.xml

