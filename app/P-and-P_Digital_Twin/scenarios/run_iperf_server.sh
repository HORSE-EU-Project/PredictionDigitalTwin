../cmd_container.sh internet_server "pkill iperf3"
../cmd_container.sh internet_server "timeout 30s iperf3 -s -B 192.168.0.201"
