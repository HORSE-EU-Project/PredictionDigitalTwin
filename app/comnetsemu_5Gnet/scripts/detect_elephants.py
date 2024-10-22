#!/usr/bin/env python
import requests
import json
import time

rt = 'http://127.0.0.1:8008'

flow = {'keys':'link:inputifindex,ipsource,ipdestination','value':'bytes'}
requests.put(rt+'/flow/pair/json',data=json.dumps(flow))

threshold = {'metric':'pair','value':10000000/8,'byFlow':True,'timeout':1}
requests.put(rt+'/threshold/elephant/json',data=json.dumps(threshold))

eventurl = rt+'/events/json?thresholdID=elephant&maxEvents=10&timeout=60'
eventID = -1
while 1 == 1:
  r = requests.get(eventurl + "&eventID=" + str(eventID))
  if r.status_code != 200: break
  events = r.json()
  if len(events) == 0: continue

  eventID = events[0]["eventID"]
  events.reverse()
  for e in events:
    print("Potential attack detected:")
    print( e['flowKey'] )
    # Create message to DEME
    url = 'http://192.168.130.9:65123'
    headers = {'Content-Type': 'application/json'}
    data = open('/home/vagrant/comnetsemu/app/comnetsemu_5Gnet/scripts/DEME_interface/sample-DoS.json', 'rb').read()
    response = requests.post(url, headers=headers, data=data)
    print("\n")
    print("URL:", url)
    print("Headers:", headers)
    print("Payload:", data)
    print("DEME Response:", response.status_code)
    #print(response.text)
    # Alternative command by shell
    #curl --location 'http://192.168.130.9:65123' --header 'Content-Type: application/json' --data @DEME_interface/sample-DoS.json
    time.sleep(30)
