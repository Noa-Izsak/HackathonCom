import socket

c = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
c.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
c.bind(("", 13117))
while True:
    data, addr = c.recvfrom(1024)
    print("received message: %s"%data)