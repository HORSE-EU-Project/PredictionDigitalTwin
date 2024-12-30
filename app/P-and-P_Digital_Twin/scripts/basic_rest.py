import socket

# Define the host and the port for the server
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

# Create a socket object
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Bind the socket to the host and port
    s.bind((HOST, PORT))
    # Enable the server to accept connections
    s.listen()
    print(f"Server is listening on {HOST}:{PORT}")

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
