curl -X 'POST' \
  'http://192.168.130.28:9898/receive-data/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "prediction": "DDoS",
    "confidence": 0.5
  }
]'
echo

