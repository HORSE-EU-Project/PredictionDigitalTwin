To record some pcap files:
./enter_container.sh dns_s
iperf3 -s -B 192.168.0.200
./enter_container.sh ue1
iperf3 -B 10.46.0.3 -c 192.168.0.200
sudo tcpdump -i s1-s2 -w prova.pcap
sudo tcpreplay -i s1-s2 prova.pcap  

sudo tcpdump -i s3-dns -w dns.pcap
sudo tcpreplay -i s3-dns dns.pcap


Most effective:
./enter_container ue1
tcpdump -i uesimtun0 -w ping.pcap
ping -I uesimtun0 -i 0.01 192.168.0.200

tcpreplay -i uesimtun0 ping.pcap

./enter_container dns_s
tcpdump -i dns-s-eth1


