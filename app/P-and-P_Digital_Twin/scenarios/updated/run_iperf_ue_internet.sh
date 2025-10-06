../../cmd_container.sh internet_server "timeout 1m iperf3 -s -B 192.168.0.201" > output.log 2>&1 &
../../cmd_container.sh ue1 "iperf3 -B 10.45.0.4 -c 192.168.0.201" > output.log 2>&1
