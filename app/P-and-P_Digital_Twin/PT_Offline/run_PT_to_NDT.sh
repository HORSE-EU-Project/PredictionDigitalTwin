./system_launcher_v2.sh
echo "[HORSE P&P NDT] Replicating real and predicted flows on the NDT"
cd generate_scenario
./run_flow_generation.sh
./run_DT_flows.sh
sleep 10
cd ..
