echo "Logging in..."
docker login azure

echo "Entering context and running the container..."
# docker context create aci myacicontext
docker context ls
docker context use myacicontext
docker --context myacicontext run -p 80:80 -p 6969 -p 861 registry.hub.docker.com/granelli/measure python3 webserver.py 80
echo "...DONE"

#echo "OXYS server located at IP:"
#docker inspect -f 
'{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' granelli/measure

