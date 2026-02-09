export ADMIN_TOKEN="a-very-strong-secret"
uvicorn whitelist_blacklist:app --host 192.168.130.9 --port 8443 \
  --ssl-certfile ./cert.pem --ssl-keyfile ./key.pem
