mininetFastAPI: A REST API for mininet/comnetsemu

Description
At the moment the FastAPI allows to:
- get a list of the mininet nodes.
- get a list of the mininet hosts.
- get a list of the mininet switches.
- get a list of the mininet links.
- get the interfaces of a node.
- execute a command in a node.

Implementation
An additional MininetRest class is defined to implement the FastAPI wrapper for mininet.
The file demo.py provides an example to run a simple topology.
You can run the demo using: sudo python3 demo.py
You can interact through REST APIs connecting to IP address 192.168.206.3 and port 8000.
Point your browser to 192.168.206.3:8000/docs for swagger interface.

Dependencies
- mininet: see http://mininet.org/download/ , or
- comnetsemu: see https://git.comnets.net/public-repo/comnetsemu/
- FastAPI framework in Python3 is required.
- pip3 install fastapi
- pip3 install uvicorn

Author
Fabrizio Granelli (fabrizio.granelli@unitn.it)

Acknowledgements
This work is supported by HORSE project: horse-6g.eu
This work is inspired by the work by Carlos Giraldo: https://github.com/cgiraldo/mininetRest

