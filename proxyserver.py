#!/usr/bin/env python3
import socket
from types import ModuleType
import sys
import threading
import logging
from collections import OrderedDict, namedtuple
import asyncio
import errno
import base64


HOST = "127.0.0.1"
PORT = 9995
LISTEN = 10
FAILURE = 1
MAX_REQUEST_BYTES = 8192 # HTTP 1.1

logging.basicConfig(format='[%(asctime)s] %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')


class DestinationRequired(Exception):
   pass

class PortInUseException(Exception):
   pass


class Socket(socket.socket):
   def __init__(self, *args, **kwargs):
      super(Socket, self).__init__(*args, **kwargs)
      self.sock = None
   
   def tcp_socket(self):
      self.sock = Socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      return self.sock
   
   def settimeout(self, value):
      if value > 30:
         raise ValueError(
            'Set max timeout 30 seconds.'
         )
      return super().settimeout(value)
   
   def udp_socket(self):
      raise NotImplementedError(
         'implement `udp_socket` if needed'
      )
   

class AsyncTCPConnection(Socket):
   __listen  = 10

   def __init__(self, host, port):
      self.host = host
      try:
         self.port = int(port)
      except ValueError:
         sys.stderr.write('Port should be an integer!\nConnection abort')
         sys.exit(1)

   async def __aenter__(self):
      try:
         self.tcp_socket.bind((self.host, self.port))
         self.tcp_socket.listen(self.__listen)
         self.settimeout(20)
         logging.info(f"Listening on {self.host}:{self.port}")
         return self.tcp_socket
      except socket.error as err:
         # just catch the errors which caused by
         # invalid address, insufficient port permisstions
         # raise error with clear message
         # Ignore others errors as no need to catch exception, just raise it.
         if err.errno == errno.EACCES:
            msg = 'Pemission denied! Run the script as an administrator'
            raise DestinationRequired(msg)
         elif err.errno == errno.EADDRINUSE:
            msg = 'Port already in use! Change or kill the running port.'
            raise PortInUseException(msg)
         else:
            raise err

   async def __aexit__(self, *args):
      if self.tcp_socket:
         logging.info("Closing connection")
         self.tcp_socket.__exit__(*args)



class InvalidRequest(Exception):
   pass


class DNSLookupError(Exception):
   pass


class BaseRequest:
   _methods = OrderedDict({
      'get':'GET',
      'post':'POST',
      'put':'PUT',
      'delete':'DELETE',
      'connect': 'CONNECT'

   })
   
   def __init__(self, request, acsii=None):
      self.header = None
      self._encoding = acsii if acsii else 'utf-8'
      self._request = request
   
   def get_headers(self):
      return self._request.decode(self._encoding).split('\r\n')
         
   def gethostbyname(self, host):
      try:
         return socket.gethostbyname(host)
      except socket.error:
         raise DNSLookupError(
            'Cannot resolve ip address! Dns lookup failed.'
         )
      
   def scheme(self):
      raise NotImplementedError()
   
   def encoding(self):
      return self._encoding
   
   @property
   def method(self):
      return self._methods.get(self.getmethod().lower(), None)


class Request(BaseRequest):
   """
   TODO: Handles request, prepare headers, Auth, cookies and etc.
   """
   def __init__(self, request, scheme='basic', decode=base64.b64decode):
      super().__init__(request)
      self.auth_scheme = scheme
      self.decode = decode
      self._requestline = namedtuple('Line', 'method url protocol')
      
   def headers(self) -> list:
      try:
         return self.get_headers()
      except Exception as decode_error:
         raise decode_error(
            f'Used encoding {self.encoding}'
         )

   @property
   def extract_request_line(self):
      method, url, protocol, rm = str(self.headers[0]).split()
      return self._requestline(method, url, protocol)

   def getmethod(self):
      return self.extract_request_line.method

   @property
   def geturl(self):
      url = self.extract_request_line.url.split('://')[-1]
      remote_url = url.split(':')
      if len(remote_url) == 2:
         host, port = remote_url
         return (str(host), int(port))

      elif len(remote_url) == 1:
         return (str(remote_url[0]), None)
      else:
         return (str(url), None)


   def get_auth(self):
      proxy_auth = None
      for string in self.headers:
         if 'Proxy-Authorization' in string:
            proxy_auth = string
            break
      if not proxy_auth:
         return False
      return proxy_auth.split()

   def auth_scheme(self):
      assert self.get_auth() > 2
      assert self.get_auth[1].lower() == self.auth_scheme, (
         'Unsupported auth scheme.'
      )

   def formatted(self):
      method = self.extract_request_line.method
      url = self.extract_request_line.url
      protocol = self.extract_request_line.url
      if 'http' in protocol.lower():
         protocol = 'HTTP/1.1'
      if not 'http' or 'https' in str(url):
         if url.startswith('www'):
            url = f'https://{url}'
         else:
            url = f'https://www.{url}'
      host, _ =self.geturl
      client_rq = f'{method} {url} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: python-requests/2.22.0\r\nAccept-Encoding: gzip, deflate\r\nAccept: */*\r\nConnection: keep-alive\r\n\r\n'
      return client_rq.encode('utf-8')


   def credentials(self):
      crd = self.get_auth()[-1]
      try:
         return self.base64_decode(crd)
      except Exception:
         return (None,
                 None)


   def base64_decode(self, data):
      try:
         data = self.decode(data).decode()
      except UnicodeDecodeError:
         pass
      username, password, *rm = data.split(':')
      return (
         username,
         password,
      )

   def auth_check(self):
      pass


class ProxyServer:
   def __init__(self, host, port):
      self.host = host
      self.port = port
      self.sock = None

   def send(self):
       pass

   def connect(self):
       pass

   def proxy_handler(self, client_socket):
      request = client_socket.recv(MAX_REQUEST_BYTES)
      r = Request(
         request=request
      )

      if not r.method:
         raise InvalidRequest(
            f'{r.getmethod()} not allowed'
         )
      host, port = r.geturl
      if not port:
         port = 80
      request = r.formatted()

      ip = None
      try:
         ip = socket.gethostbyname(host)
      except socket.error:
         raise DNSLookupError

      assert ip, (
         'Cannot resolve ip address.'
      )
       # Remote server socket
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect((ip, port))
      s.sendall(request)
      while True:
          data = s.recv(4096)
          if (len(data) > 0):
              client_socket.send(data)
          else:
              break

   async def _runprocess(self):
      async with AsyncTCPConnection(host=self.host, port=self.port) as connection:
         terminate = False
         while not terminate:
            client, _ = connection.accept()
            d = threading.Thread(target=self.proxy_handler, args=(client, ))
            d.setDaemon(True)
            d.start()

   def start(self):
      self.loop.run_until_complete(self._runprocess())
