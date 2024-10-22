import requests

url = 'http://192.168.130.9:65123'
headers = {'Content-Type': 'application/json'}
data = open('DEME_interface/sample-DoS.json', 'rb').read()

response = requests.post(url, headers=headers, data=data)

print(url, headers, data)
print(response.status_code)
#print(response.text)
