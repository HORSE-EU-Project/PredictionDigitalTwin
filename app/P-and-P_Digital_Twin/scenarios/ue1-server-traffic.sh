./run_iperf_server.sh internet_server 192.168.0.201 &
sleep 10
./run_iperf_ips.sh ue1 10.45.0.4 192.168.0.201

