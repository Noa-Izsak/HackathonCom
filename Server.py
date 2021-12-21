import socket
from time import sleep

ip = "127.0.0.1"

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, ip)
    # Set a timeout so the socket does not block
    # indefinitely when trying to receive data.
    server.settimeout(0.2)
    server.bind(("", 44444))
    message = b"your very important message"
    while True:
        server.sendto(message, ('<broadcast>', 13117))
        print("message sent!")
        sleep(1)

if __name__ == "__main__":
    main()