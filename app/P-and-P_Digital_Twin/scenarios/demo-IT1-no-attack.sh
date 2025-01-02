echo "[ Starting demo scenario ]"
echo "Activating tcpdump"
sudo tcpdump -i s3-internet -w ../data/trace-%m-%d-%H-%M-%S-%s.pcap -W 1 -G 30 &
echo "Setting internet_server as destination"
./run_iperf_server.sh &
sleep 1
#echo "Activating background data flow"
./run_iperf_n_flows.sh &
sleep 10
#echo "Starting attack"
#./flood.sh &
sleep 25
echo "Starting prediction"
cd ../scripts/
./find_most_recent.sh
cd ../scenarios/

