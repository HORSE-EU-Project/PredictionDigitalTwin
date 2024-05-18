import requests

requests.post("http://localhost:1236/digitaltwin",
  data="Backup successful 😀".encode(encoding='utf-8'))
