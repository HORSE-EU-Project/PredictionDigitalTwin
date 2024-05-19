#!/bin/bash

docker exec -i $(docker ps -aq -f "name=^$1$") /bin/bash -c "$2"

