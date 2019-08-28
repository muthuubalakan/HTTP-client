#!/usr/bin/env python3	
import socket	
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


class AsyncTCPConnection:
   __listen  = 10
   log = True
   
   def __init__(self, host, port, log=log):
      self.host = host
      try:
         self.port = int(port)
      except ValueError:
         sys.stderr.write('Port should be an integer!\nConnection abort')
         sys.exit(1)
      
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

   
   def __repr__(self):
      return f'{type(self).__name__}(connection={self.tcp})'
      
   async def __aenter__(self):
      try:
         self.sock.bind((self.host, self.port))
         self.sock.listen(self.__listen)
         logging.info(f"Listening on {self.host}:{self.port}")
         return self.sock
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
      if self.sock:
         logging.info("Closing connection")
         self.sock.__exit__(*args)



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
   
   @property
   def method(self):
      return self._methods.get(self.getmethod().lower(), None)


class Request(BaseRequest):
   """
   TODO: Handles request, prepare headers, Auth, cookies and etc.
   """ 
   def __init__(self, request, **kwargs):
      super().__init__()
      self.auth_scheme = 'basic'
      self.decode = base64.b64decode
      try:
         self.headers = request.decode('utf-8').split('\r\n')
      except Exception:
         raise UnicodeDecodeError
   
   @property 
   def extract_request_line(self):
      request_line = namedtuple('Line', 'method url protocol')
      data = str(self.headers[0]).split()
      assert len(data) == 3 
      # method, url, protocol
      method = data[0]
      url = data[1]
      protocol = data[2]
      return request_line(method, url, protocol)
   
   def getmethod(self):
      return self.extract_request_line.method
   
   def geturl(self):
      url = self.extract_request_line.url.split('://')
      remote_url = url[-1]
      return remote_url
      
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
      self.loop = asyncio.get_event_loop()
      
   async def proxy_handler(self, client_socket):
      request = client_socket.recv(MAX_REQUEST_BYTES)
      r = Request(
         request=request
      )
      

      if not r.method:
         raise InvalidRequest(
            f'{r.getmethod()} not allowed'
         )
      ip = None
      try:
         ip = socket.gethostbyname(r.geturl)
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
      terminate = False
      async with AsyncTCPConnection(host=self.host, port=self.port) as connection:
         client, _ = connection.accept()
         logging.info(_)
         while not terminate:
            try:
               await self.proxy_handler(client)
            except Exception:
               terminate = True
               
   def start(self):
      self.loop.run_until_complete(self._runprocess())
      self.loop.close()