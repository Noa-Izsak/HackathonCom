import errno
import multiprocessing
import socket
import threading
from random import *
from threading import Thread
import time
from time import sleep
import copy

CLIENT_COUNT_TO_START_GAME = 2
GAME_DURATION = 10
BUFFER_SIZE = 1024
RANKS_TO_PRINT = 3


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_in_color(color, string):
    print(color + string + bcolors.ENDC)


def checkSocketIsClosed(s):
    try:
        str1 = s.recv(BUFFER_SIZE)
        return len(str1) == 0
    except socket.error as e:
        err = e.args[0]
        if not (err == errno.EAGAIN or err == errno.EWOULDBLOCK):
            return True
    except:
        print("other error")
    return False


class Game:
    startTime = 0

    def __init__(self):
        self.done = False
        pass

    def timePassed(self):
        return time.time() - self.startTime > GAME_DURATION

    def setTime(self):
        self.startTime = time.time()


class MyServer:
    hostname = socket.gethostname()
    #ip = socket.gethostbyname(hostname)
    ip = "172.1.0.111"
    serverPort = 3500
    clientCount = 0
    state = 0  # 0 = waiting, 1 = playing
    clients = []
    amountOfDraws = 0
    winners = {}
    losers = {}
    server = None

    def __init__(self):
        pass

    def on_new_client(self, clientsocket, addr):
        print_in_color(bcolors.OKCYAN, "new client connected")
        if self.state == 1:
            clientsocket.close()
            return
        msg = clientsocket.recv(BUFFER_SIZE)
        name = msg.decode()
        self.clientCount += 1
        self.clients.append([name, clientsocket])
        if self.clientCount == CLIENT_COUNT_TO_START_GAME:
            self.start_game()

    def send_to_everyone(self, msg):
        for client in self.clients:
            try:
                client[1].send(msg)
            except socket.error as e:
                pass

    def start_game(self):
        self.state = 1
        n1 = randint(0, 9)
        n2 = randint(0, 9 - n1)
        msg = (
                "Welcome to Quick Maths. \nPlayer 1: %sPlayer 2: %s==\nPlease answer the following question as fast as you can:\nHow much is %s+%s?" % (
            self.clients[0][0], self.clients[1][0], n1, n2)).encode()
        self.send_to_everyone(msg)
        ans = n1 + n2
        game = Game()
        game.setTime()
        t1 = threading.Thread(target=self.wait_for_ans, args=(self.clients[0], self.clients[1], ans, game))
        t2 = threading.Thread(target=self.wait_for_ans, args=(self.clients[1], self.clients[0], ans, game))
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        if not game.done:
            self.finish_game(None, None, ans, game)
        pass

    def wait_for_ans(self, client, otherClient, realAns, game):
        msg = []
        while len(msg) == 0:
            if game.timePassed():
                return
            if game.done:
                return
            try:
                msg = client[1].recv(BUFFER_SIZE)
            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    sleep(0.1)
                    continue
                else:  # Error, finish the game in a draw
                    self.finish_game(None, None, realAns, game)
        clientAns = msg.decode()
        if str(realAns) == clientAns:
            self.finish_game(client, otherClient, realAns, game)
        else:
            self.finish_game(otherClient, client, realAns, game)
        return

    def finish_game(self, winner, loser, ans, game):
        game.done = True
        if winner is None:
            self.amountOfDraws += 1
            msg = "Game over!\nThe correct answer was %s!\nThe game finished in a draw." % ans
        else:
            self.winners[winner[0]] = self.winners.get(winner[0], 0) + 1
            self.losers[loser[0]] = self.losers.get(loser[0], 0) + 1
            msg = "Game over!\nThe correct answer was %s!\nCongratulations to the winner: %s" % (ans, winner[0])
        self.send_to_everyone(msg.encode())
        self.state = 0
        self.clientCount = 0
        self.clients = []
        # for c in self.clients:
        # c[1].close()
        print_in_color(bcolors.OKBLUE, "Game over, sending out offer requests...")
        self.print_stats()
        self.broadcast(self.server)
        return

    def print_stats(self):
        if len(self.winners) > 0:
            print_in_color(bcolors.BOLD + bcolors.UNDERLINE, "Top 3 winners are:")
            ranks = sorted(self.winners.items(), key=lambda item: item[1])[::-1]
            i = 0
            for w in ranks:
                print(w[0][:-1] + " : %s \n" % (str(w[1])))
                i += 1
                if i >= RANKS_TO_PRINT:
                    break

        if len(self.losers) > 0:
            ranks_los = sorted(self.losers.items(), key=lambda item: item[1])[::-1]
            print_in_color(bcolors.BOLD + bcolors.UNDERLINE, ("The biggest loser is: %s" % (ranks_los[0][:-1])))

        print_in_color(bcolors.BOLD, "Amount of draws in total : %s" % str(self.amountOfDraws))

    def start_tcp_server(self):
        s = socket.socket()  # Create a socket object
        s.bind((self.ip, MyServer.serverPort))
        print_in_color(bcolors.OKGREEN, ("Server started, listening on IP address %s" % self.ip))

        s.listen(5)
        while True:
            c, addr = s.accept()
            c.setblocking(False)
            t1 = threading.Thread(target=self.on_new_client, args=(c, addr))
            t1.start()

    def main(self, ):
        x = threading.Thread(target=self.start_tcp_server, args=())
        x.start()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.server.settimeout(0.2)
        self.server.bind((self.ip, 44444))
        self.broadcast(self.server)

    def checkAndRemoveClosedClients(self):
        self.clients = [c for c in self.clients if not (checkSocketIsClosed(c[1]))]
        self.clientCount = len(self.clients)

    def broadcast(self, server):
        while self.state == 0:
            print(self.clientCount)
            self.checkAndRemoveClosedClients()
            message = (0xabcddcba).to_bytes(4, 'big', signed=False)
            message += (2).to_bytes(1, 'big')
            message += MyServer.serverPort.to_bytes(2, 'big')
            server.sendto(message, ('<broadcast>', 13117))
            sleep(1)


if __name__ == "__main__":
    s = MyServer()
    s.main()
