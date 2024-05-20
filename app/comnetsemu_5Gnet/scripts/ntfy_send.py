import requests

requests.post("http://localhost:8086/digitaltwin",
  data="Backup successful 😀".encode(encoding='utf-8'))
