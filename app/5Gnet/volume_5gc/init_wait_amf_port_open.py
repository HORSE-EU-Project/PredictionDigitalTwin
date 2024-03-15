import sys, socket, time


if __name__ == "__main__":

    ip   = sys.argv[1]
    port = int(sys.argv[2])

    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_SCTP)
    location = ( ip, port)
    while True:
        time.sleep(0.1)
        result_of_check = a_socket.connect_ex(location)
        # print("-----------------")
        # print(result_of_check)
        if result_of_check == 0:
            break