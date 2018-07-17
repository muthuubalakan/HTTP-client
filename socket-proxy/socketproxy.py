#!/usr/bin/env python3
#
#
# Socketproxy: connection through proxy

import socket
import base64
import sys


# Exit failure
EXIT = 1

# Default port
# HTTP request
PORT = 80

# Allowed requests
requests = ['GET', 'POST', 'DELETE']

# Python3 requried
assert sys.version_info >= (3, 0)


class Socketproxy:
    """Socketproxy make a request beyond proxy

    socket proxy uses socket to make a request
    Arguments:
        proxy --- [Proxy]
                  proxy with full address(includes username and password)
                  ex. "http://username:password@proxy-server.net:port"
    Usage:
        Socketproxy(proxy, "www.example.com")
    """

    def __init__(self, proxy, remote_host, remote_port=None):
        self.remote_host = remote_host
        self.remote_port = remote_port
        self._credentials, self._proxy_server = self.url_parser(proxy)

    def url_parser(self, proxy):
        """Return _credentials and proxyserver"""
        if not isinstance(proxy, str):
            sys.stderr.write("Enter a valid proxy")
            sys.exit(EXIT)
        proxy = proxy.split("//")[1]
        credentials = proxy.split('@')[0].split(':')
        proxy_server = proxy.split('@')[1].split(':')
        return credentials, proxy_server

    def check_proxy(self):
        if not (isinstance(self._credentials, list)
                and isinstance(self._proxy_server, list)):
            sys.stderr.write("Proxy should be a str\n"
                             "EXIT now\n")
            sys.exit(EXIT)
        return True

    def proxy_entry(self):
        """Returns decoded string"""
        if not self.check_proxy:
            return False
        if len(self._credentials and self._proxy_server) != 2:
            print("User credentials and proxysever host, port required")
            sys.exit(EXIT)

        username, password = self._credentials[0], self._credentials[1]
        authorize = base64.b64encode((username+':'+password).encode('utf-8'))
        return authorize.decode('utf-8')

    def headers(self):
        if not self.remote_port:
            self.remote_port = PORT
        if not self.remote_host.startswith('www.' or 'http//' or 'https'):
            self.remote_host = 'www.'+self.remote_host
        # Headers
        authorize = 'Proxy-Authorization: Basic '+self.proxy_entry()+'\r\n'
        user_agent = 'User-Agent: python\r\n'
        request = 'CONNECT %s:%s HTTP/1.0\r\n' % (self.remote_host,
                                                  self.remote_port)
        request = request+authorize+user_agent+'\r\n'
        return request

    def make_request(self, method):
        if not self.remote_port:
            self.remote__port = None
        request = """%s http://%s HTTP/1.1\r\nHost: %s\r\n\r\n""" % (method.upper(), self.remote_host, self.remote_host)
        return request.encode('utf-8')

    def connect(self, method):
        if method not in requests:
            print("Invalid request")
            sys.exit(EXIT)
        request = self.headers()
        proxy_host, proxy_port = self._proxy_server[0], self._proxy_server[1]
        if not isinstance(proxy_port, int):
            proxy_port = int(proxy_port)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((proxy_host, proxy_port))
        sock.send(request.encode('utf-8'))
        response = sock.recv(20)
        response_status = response.decode('utf-8').split('/')[1].split()[1]
        if int(response_status) != 200:
            print("Error: {}".format(response_status))
            sys.exit(EXIT)
        sock.sendall(self.make_request(method))
        data = sock.recv(69829)
        print(data)
