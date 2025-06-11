echo "[HORSE] Activating EM Interface"
cd ./HORSE_EM_interface/
./run_EM_interface.sh &
sleep 10
./monitor_file_UMU.sh ./last.xml

