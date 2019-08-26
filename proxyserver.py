#!/usr/bin/env python3	
import socket	
import sys	
import threading	
import logging
from collections import OrderedDict


HOST = "127.0.0.1"
PORT = 8080
LISTEN = 10
FAILURE = 1
MAX_REQUEST_BYTES = 8192 # HTTP 1.1

logging.basicConfig(format='[%(asctime)s] %(levelname)-8s %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')


class InvalidRequest(Exception):
   pass


class BaseRequest:
   _methods = OrderedDict({
      'get':'GET',
      'post':'POST',
      'put':'PUT',
      'delete':'DELETE'
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
      self._request = request

   def getmethod(self):
      return str(self.headers[0])
   
   def url(self):
      return self.headers[1]
   
   @property
   def headers(self):
      return self._request.decode('utf-8').split()


class TCPConnection:

   def __init__(self, host=HOST, port=PORT):	
      self._host = host
      try:
         self._port = int(port)
      except ValueError:
         logging.error(f"Port assign failed! Setting port to {PORT}")
         self._port = PORT
      
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   
   def __enter__(self):
      """Magic"""
      try:
         self.sock.bind((self._host, self._port))
         self.sock.listen(LISTEN)
         logging.info(f'Listening on {self._host}:{self._port}')
         return self.sock
      except socket.error as err:
         logging.error(err)
   
   def __exit__(self, *args):
      self.sock.close()

   def __repr__(self):
      return f'{type(self).__name__}({self.sock})'

   def proxy_handler(self, client_socket):	
      request = client_socket.recv(MAX_REQUEST_BYTES)
      r = Request(
         request=request
      )

      if not r.method:
         raise InvalidRequest(
            f'{r.getmethod()} not allowed'
         )

       # Remote server socket	
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	
      s.connect((r.url, 80))	
      s.sendall(request)	
      while True:	
          data = s.recv(4096)	
          if (len(data) > 0):	
              client_socket.send(data)	
          else:	
              break	

   def start(self):	
      with self as sock:
         while True:
            try:
               client_socket, _ = sock.accept()	
               proxy_thread = threading.Thread(target=self.proxy_handler,	
                                            args=(client_socket,))
               proxy_thread.start()
            except KeyboardInterrupt:
               # kill it
               sock.close()
               logging.error("Stopping server!")
               break
         sys.exit(FAILURE)