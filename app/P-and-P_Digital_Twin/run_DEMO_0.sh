echo "[HORSE] Activating EM Interface"
cd ./HORSE_EM_interface/
./run_EM_interface.sh &
cd ..
cd ./HORSE_DTE_interface/
while true; do
  echo "[HORSE] Contacting DTE"
  ./test_DTE_UPC.sh
  sleep 10
done
