#!/usr/bin/env python3
import socket
import sys
import threading


class TCP:
    """ Prototype of a proxy server

    Small prototype of a TCP proxy server.
    Request goes through the proxy>>>

          Client(a request usally from a web browser or from client side)
            |
            |
          Proxy(at the Middle) --Blocking -- User-managment etc.
            |
            |
          Remote server(Server ex.google.com, fb.com)

    Principle of the proxy is setting a middle man to regulate all request.
    """

    def __init__(self):
        self.host = '127.0.0.1'
        self.port = int(sys.argv[1])
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        print("Connected to ..", self.host, self.port)
        self.sock.listen(10)

    def proxy_handler(self, client_socket):
        request = client_socket.recv(1024)
        # Parse the url from the client request
        # the request url parsing method may varies
        first_line = request.split()
        url = first_line[1]
        url = url.decode('utf-8')
        url = url.replace('/', '')

        # Remote server socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((url, 80))
        s.sendall(request)
        while True:
            # Receive data, this must be a larger amount.
            data = s.recv(4096)
            if (len(data) > 0):
                client_socket.send(data)
            else:
                break

    def proxy(self):
        """Run the proxy server

        Usage:
            TCP().proxy()
        """
        while True:
            client_socket, addr = self.sock.accept()

            # You can use asyncio.
            proxy_thread = threading.Thread(target=self.proxy_handler,
                                            args=(client_socket,))
            proxy_thread.start()


if __name__ == '__main__':
    tcp = TCP()
    tcp.proxy()
