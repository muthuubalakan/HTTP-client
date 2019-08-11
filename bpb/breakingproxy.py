#!/usr/bin/env python3
# coding: utf-8
import socket
import base64
import asyncio
import sys
import logging
from urllib.parse import urlparse
from collections import namedtuple


EXIT = 1
PORT = 80
MAX = 2064

ALLOWED_REQUESTS = ['GET', 'POST', 'PUT', 'DELETE']


assert sys.version_info >= (3, 0), (
        'Requires python3 to run `BreakingProxy`.'
        ' No Python2 support.')


class ArgumentException(Exception): pass


class BreakingProxy:
    
    def __init__(self, remote_host, proxy_url=None, remote_port=None, **kwargs):
        self.remote_host = remote_host
        self.remote_port = remote_port if remote_port else PORT
        self.proxy_url = proxy_url
        self.response = namedtuple('Response', 'data status')
        self.classname = type(self).__name__
        if not self.proxy_url:
            self.username = kwargs.pop('username', None)
            self.password = kwargs.pop('password', None)
            assert self.username and self.password, (
                    'Need a username and password to connect to proxy server.'
                   )
            self.proxy = kwargs.pop('proxy', None)

            assert self.proxy, (
                    'Expected proxy server address'
                    '. But got None')

    def __repr__(self):
        return f'{self.classname}(url={self.remote_host}, proxyserver={self.proxy_url})'

    def get_tuple(self, string:str) -> tuple:
        splitted_string = string.split(":")
        assert len(splitted_string) == 2, (
            'Invalid proxy server address. You need to specify Proxy server address and port'
            'Ex.proxy_server=exampleorg.net:80'
        )
        host_address = splitted_string[0]
        assert isinstance(host_address, str), (
            'Proxy server address: Expected string. '
            f'But got {type(host_address).__class__.__name__}.'
        
        )
        try:
            port = int(splitted_string[1])
        except ValueError:
            raise ArgumentException(
        'Invalid port. Port should be an int.'
        )
        return (host_address, port)

    @property
    def get_proxy_credentials(self):
        proxy_credentials = namedtuple('Credentials',
                                       'username password proxy_host proxy_port')
        
        if not hasattr(self, 'proxy_url'):
            print("Called")
            proxy_host, proxy_port = self.get_tuple(self.proxy)
            return proxy_credentials(self.username, self.password, proxy_host, proxy_port)

        parsed_url = urlparse(self.proxy_url)
        assert parsed_url.scheme.lower() == 'http' or 'https', (
            'Expected http or https proxy.'
            f'But got {parsed_url.scheme}!'
        )
        credentials = parsed_url.netloc.split('@')[0].split(':')
        proxy_server = parsed_url.netloc.split('@')[1]
        proxy_host, proxy_port = self.get_tuple(proxy_server)
        return proxy_credentials(credentials[0], credentials[1], proxy_host, proxy_port)

    @property
    def proxy_entry(self):
        proxy_credentials = self.get_proxy_credentials
        authorize = base64.b64encode((proxy_credentials.username+':'+proxy_credentials.password).encode('utf-8'))
        return authorize.decode('utf-8')

    def _get_headers(self, proxy_entry):
        if not self.remote_host.startswith('www.' or 'http//' or 'https'):
            self.remote_host = 'www.'+ self.remote_host

        authorize = 'Proxy-Authorization: Basic ' + proxy_entry + '\r\n'
        user_agent = 'User-Agent: python\r\n'
        request = 'CONNECT %s:%s HTTP/1.0\r\n' % (self.remote_host,
                                                  self.remote_port)
        return request + authorize + user_agent + '\r\n'   

    def make_request(self, method):
        if not self.remote_port:
            self.remote__port = None
        request = """%s http://%s HTTP/1.1\r\nHost: %s\r\n\r\n""" % (method.upper(), self.remote_host, self.remote_host)
        return request.encode('utf-8')

    def connect(self, method):
        assert method in ALLOWED_REQUESTS, (
            f'Cannot make `{method}` request.!'
            f'`{self.classname}` can only make {ALLOWED_REQUESTS} requests.'
        )

        request = self._get_headers(self.proxy_entry)
        proxy_credentials = self.get_proxy_credentials

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((proxy_credentials.proxy_host, proxy_credentials.proxy_port))
        sock.send(request.encode('utf-8'))
        response = sock.recv(20)
        response_status = response.decode('utf-8').split('/')[1].split()[1]
        if int(response_status) != 200:
            logging.error("Error: {}".format(response_status))
            sys.exit(EXIT)
        sock.sendall(self.make_request(method))
        resp = ''
        while sock.recv:
            resp + sock.recv(MAX)
        return self.response(resp, response_status)