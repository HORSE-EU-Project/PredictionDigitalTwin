curl -X 'POST' \
  'http://10.208.11.73:9898/receive-data/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "prevention": "dns_amplification",
    "confidence": 0.5
  }
]'
echo
python3 ./HORSE_dashboard/update_senderv2.py box3 green "Message to DTE Sent"
