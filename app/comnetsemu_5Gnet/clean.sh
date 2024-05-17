#!/bin/bash

sudo mn -c

echo "*** Stopping all containers"
docker stop $(docker ps -aq)
docker container prune -f
docker rm $(sudo docker ps -a -q) -f

if [ "$1" == "log" ]; then
    rm log/*.log 
fi

if [ "$1" == "data" ]; then
    rm data/*
fi

# Get all network links that contain the string 'ceos'
echo "*** Removing all links"
links=$(ip link | grep -oP '(?<=: )ceos[^:]*')

# Loop through each link and delete it
for link in $links; do
    sudo ip link delete "$link"
done

# Kill sFlow
echo "*** Stopping sFlow"
pkill java

# Find all processes containing 'dt_app' and kill them
echo "*** Stopping any GUI"
pgrep -f 'dt_app' | while read -r pid; do
    echo "Killing process with PID $pid"
    kill -9 "$pid"
done
