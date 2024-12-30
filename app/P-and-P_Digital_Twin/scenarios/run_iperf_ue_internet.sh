../cmd_container.sh internet_server "iperf3 -s -B 192.168.0.201" > output.log 2>&1 &
../cmd_container.sh ue "iperf3 -B 10.45.0.11 -c 192.168.0.201" > output.log 2>&1
