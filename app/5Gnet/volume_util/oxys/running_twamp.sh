echo "+------------------------------------------------+"
echo "| OXYS TWAMP client/server docker implementation |"
echo "+------------------------------------------------+"

echo "\nRunning Client and Server locally"
docker network prune
docker run -dit --name OXYS-client -p 8080:80 -p 8081:8000 oxys-reflector bash
docker run -dit --name OXYS-server -p 8082:80 -p 6969 oxys-reflector bash
docker network connect bridge OXYS-client
docker network connect bridge OXYS-server

echo "\nTesting Internet connectivity"
docker exec OXYS-client ping -c3 8.8.8.8
docker exec OXYS-client ifconfig eth0
docker exec OXYS-server ifconfig eth0
docker exec OXYS-client ping -c3 172.17.0.3

echo "\nActivating webservers"
docker exec OXYS-client python3 webserver.py 80 &
docker exec OXYS-server python3 webserver.py 80 &
echo "OXYS server located at IP:"
IP_ADDR=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' OXYS-server)
IP_ADDR+=":861"
echo $IP_ADDR
sleep 1

echo "\nRunning TWAMP... please wait"
#docker exec OXYS-server python3 ./twamp.py responder $IP_ADDR &
docker exec OXYS-server python3 ./twamp.py responder 0.0.0.0:861 &
docker exec OXYS-client python3 ./twamp.py sender $IP_ADDR

echo "\nRunning IPERF3... please wait"
docker exec OXYS-server python3 ./iperf-server.py &
sleep 2
docker exec OXYS-client python3 ./iperf-client.py

echo "\nActivating file access"
docker exec OXYS-client python3 -m http.server 8000 &

# echo "\nStopping all containers"
# docker stop $(docker ps -aq) > NULL
# docker rm $(docker ps -aq) > NULL
