echo "[ {"
echo " \"prevention\": \"ddos_downlink\", "
echo " \"confidence\": 0.5"
echo "} ]"
curl -X 'POST' \
  'http://10.19.2.1:9898/receive-data/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "prevention": "ddos_downlink",
    "confidence": 0.5
  }
]'
echo
echo
