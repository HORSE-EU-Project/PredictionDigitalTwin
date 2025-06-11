curl -X 'POST' \
  'http://10.208.11.73:9898/receive-data/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "prediction": "Data Breach",
    "confidence": 1.0
  }
]'
echo

