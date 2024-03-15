import iperf3

server = iperf3.Server()
# server.bind_address = '127.0.0.1'
server.bind_address = '172.17.0.3'
server.port = 6969
server.verbose = True
server.json_output = True
while True:
	server.run()

