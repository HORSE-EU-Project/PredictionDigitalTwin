echo "[HORSE SAN] Predicting traffic..."
docker cp upf_cld:/open5gs/capture.pcap data/trace-last.pcap
cd scripts
./predict_traffic.sh
cd ..
echo "[HORSE SAN] Prediction complete"
