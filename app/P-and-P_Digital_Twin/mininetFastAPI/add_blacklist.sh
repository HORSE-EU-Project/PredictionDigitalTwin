curl -X POST "https://192.168.130.9:8443/clients/blacklist" \
  -H "X-Admin-Token: a-very-strong-secret" \
  -H "Content-Type: application/json" \
  -d '{"entries": ["203.0.113.5", "198.51.100.0/24"]}'
