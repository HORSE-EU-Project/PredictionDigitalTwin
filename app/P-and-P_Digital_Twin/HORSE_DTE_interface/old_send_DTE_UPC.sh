#!/bin/bash

# The URL for the POST request
URL="http://10.19.2.12:9898/receive-data/"

# The JSON data to be sent. We are taking only the first object from your file.
JSON_DATA='{
    "detection": [
        {
            "attack": "DDoS",
            "accuracy": 0.93
        }
    ],
    "node": "DNS_server"
}'

# The cURL command
curl -X POST -H "Content-Type: application/json" -d "$JSON_DATA" "$URL"
