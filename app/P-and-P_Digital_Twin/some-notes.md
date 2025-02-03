To record some pcap files:
./enter_container.sh dns_s
iperf3 -s -B 192.168.0.200
./enter_container.sh ue1
iperf3 -B 10.46.0.3 -c 192.168.0.200
sudo tcpdump -i s1-s2 -w prova.pcap
sudo tcpreplay -i s1-s2 prova.pcap  
