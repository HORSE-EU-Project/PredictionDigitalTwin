echo "[HORSE P&P NDT] Copying the most recent pcap file"
cd ../pcap_file_mover/
./move_latest_pcap.sh
cd ../sync_and_predict/
echo "[HORSE P&P NDT] Analyzing the input pcap file"
./flow_summary.sh /tmp/pcap_destination/current.pcap
echo "[HORSE P&P NDT] Replicating real and predicted flows on the NDT"
cd generate_scenario
./run_flow_generation_simple.sh
./run_DT_flows.sh
#echo "[HORSE P&P NDT] Waiting for the emulation to run..."
#sleep 30
echo "[HORSE P&P NDT] Emulation complete, now analyzing the resulting pcap file"
cd ..
