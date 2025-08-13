echo "[HORSE SAN] Activating traffic capture (tcpdump)"
% sudo tcpdump -i s3-internet -w ../data/trace-%m-%d-%H-%M-%S-%s.pcap -W 1 -G 30 &
echo "[HORSE SAN] Starting Iperf Server"
./run_iperf_server_ips.sh internet_server 192.168.0.201 5202 &
sleep 10
echo "[HORSE SAN] Running Client data flow"
./run_iperf_ips.sh ue1 10.45.0.4 192.168.0.201 5202

