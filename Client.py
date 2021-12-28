import errno
import multiprocessing
import os
import socket
import sys
import threading
import time
import selectors
import fcntl
import termios
import tty
import traceback

tcpSocket = None

orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)


def got_keyboard_data(stdin):
    if tcpSocket is not None:
        answer = stdin.read()
        print(answer)
        tcpSocket.send(answer.encode())

def print_in_color(color, string):
    print(color + string + bcolors.ENDC)

class bcolors:
    PINK = '\033[95m'
    OKBLUE = '\033[94m'
    purple = '\033[35m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def printServerRes(s):
    result, addr2 = s.recvfrom(1024)
    print_in_color(bcolors.OKBLUE+bcolors.BOLD, result.decode())
    global tcpSocket
    tcpSocket = None
    m_selector.unregister(sys.stdin)
    m_selector.unregister(s)


def clearSocket(s):
    s.setblocking(False)
    while True:
        try:
            s.recv(1024)
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                break
    s.setblocking(True)


teamName = "Champs"
Mode = 0 #0 for listening, 1 for playing
print_in_color(bcolors.purple, "Client started, listening for offer requests...")
c = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
c.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
c.bind(("", 13117))
while True:
    date = []
    data, addr = c.recvfrom(1024)
    cookie = int.from_bytes(data[0:4:1], byteorder='big', signed=False)
    messageType = int.from_bytes(data[4:5:1], byteorder='big', signed=False)
    serverPort = int.from_bytes(data[5:7:1], byteorder='big', signed=False)
    if cookie == 0xabcddcba:
        print(bcolors.PINK + ("Received offer from %s, attempting to connect..." % str(addr))+bcolors.ENDC)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((addr[0], serverPort))
                s.send((teamName + "\n").encode())
                question, addr1 = s.recvfrom(1024)
                print_in_color(bcolors.BOLD, question.decode())
                tcpSocket = s

                #
                m_selector = selectors.DefaultSelector()
                m_selector.register(sys.stdin, selectors.EVENT_READ, got_keyboard_data)
                m_selector.register(tcpSocket, selectors.EVENT_READ, printServerRes)
                old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
                while tcpSocket is not None:
                    events = m_selector.select()
                    for k, mask in events:
                        callback = k.data
                        callback(k.fileobj)
                #
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                s.close()
            except Exception:
                #print(traceback.format_exc())
                s.close()
                c.close()
                exit(0)
                pass
            tcpSocket = None
            clearSocket(c)
            print("Server disconnected, listening for offer requests...")
