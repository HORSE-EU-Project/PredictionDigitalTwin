openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout key.pem \
  -out cert.pem \
  -subj "/CN=192.168.130.9" \
  -addext "subjectAltName = IP:192.168.130.9,IP:0.0.0.0"
