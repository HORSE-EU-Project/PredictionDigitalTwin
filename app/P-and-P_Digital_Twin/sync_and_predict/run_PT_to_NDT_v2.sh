echo "[HORSE P&P NDT] Analyzing the input pcap file"
./flow_summary.sh pcap/sample.pcap
echo "[HORSE P&P NDT] Replicating real and predicted flows on the NDT"
cd generate_scenario
./run_flow_generation_simple.sh
./run_DT_flows.sh
echo "[HORSE P&P NDT] Waiting for the emulation to run..."
sleep 60
echo "[HORSE P&P NDT] Emulation complete, now analyzing the resulting pcap file"
cd ..
