import socket
import requests
import datetime
import os

# Define the host and the port for the server
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65123        # Port to listen on (non-privileged ports are > 1023)

# Create a socket object
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Bind the socket to the host and port
    s.bind((HOST, PORT))
    # Enable the server to accept connections
    s.listen()
    print(f"Server is listening on {HOST}:{PORT}")

    while 1==1:

        # Wait for a connection
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                # Receive data from the client
                data = conn.recv(1024)
                if not data:
                    break
                # Print the received payload
                print(f"Received payload: {data.decode()}")
                #requests.post("http://localhost:8086/digitaltwin",
                #  data="[From Early Modeling] Notification received".encode(encoding='utf-8'))
                timestamp = str(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
                file_path = '../log/input/input.log'
                new_name = f"{os.path.splitext(file_path)[0]}_{timestamp}{os.path.splitext(file_path)[1]}"
                print(f"File renamed to: {new_name}")
                f = open(new_name, 'wt', encoding='utf-8')
                f.write(data.decode())
                f.close()

