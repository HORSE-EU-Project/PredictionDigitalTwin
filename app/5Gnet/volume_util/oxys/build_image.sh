#!/bin/bash

echo "Build docker image for OXYS Reflector"
docker build -t oxys-reflector --file ./Dockerfile .
