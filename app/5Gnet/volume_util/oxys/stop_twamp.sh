echo "+------------------------------------------------+"
echo "| OXYS TWAMP client/server docker implementation |"
echo "+------------------------------------------------+"

echo "\nStopping all containers"
docker stop $(docker ps -aq) > NULL
docker rm $(docker ps -aq) > NULL
echo "...done"
