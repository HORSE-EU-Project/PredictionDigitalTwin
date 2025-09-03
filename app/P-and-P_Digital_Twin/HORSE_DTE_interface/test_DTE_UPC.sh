curl -X 'POST' \
  'http://10.19.2.12:9898/receive-data/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "prediction": "DDoS",
    "confidence": 0.5
  }
]'
echo
echo
