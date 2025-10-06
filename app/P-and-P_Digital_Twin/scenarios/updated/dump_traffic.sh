../../cmd_container.sh internet_server "timeout 1m tcpdump -i internet-eth1 -w capture.pcap"
docker cp internet_server:/capture.pcap ./trace-capture.pcap
