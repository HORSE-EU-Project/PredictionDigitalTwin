echo "[ Starting scenario n.1 ]"
echo "Setting internet_server as destination"
./run_iperf_server.sh &
./run_iperf_server_2.sh &
sleep 2
echo "Activating first data flow"
./run_iperf_client.sh &
sleep 5
echo "Activating second data flow"
./run_iperf_client_2.sh &
