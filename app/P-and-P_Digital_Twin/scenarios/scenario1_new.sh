echo "[ Starting scenario n.1 ]"
#echo "Activating tcpdump"
#sudo tcpdump -i ceos0-eth1 -w ../data/trace-%m-%d-%H-%M-%S-%s.pcap -W 1 -G 30 &
echo "Setting internet_server as destination"
./run_iperf_server.sh &
#./run_iperf_server_2.sh &
sleep 3
echo "Activating first data flow"
./run_iperf_client_new.sh &
sleep 6
#echo "Activating second data flow"
#./run_iperf_client_2.sh &
sleep 30
#echo "Starting prediction"
#cd ../scripts/
#./find_most_recent.sh
#cd ../scenarios/
echo "Scenario complete"
