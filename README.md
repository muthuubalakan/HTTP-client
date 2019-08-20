# Breaking Proxy
Making request beyond proxy.

## About:
This is a simple HTTP client using raw TCP socket connection to make request through the proxy server.(No urllib or any other high level module). It is a cool code snippet for newbies. 

**still developing**


### TODO:
- Need text and json responses
- Parse the original status code from response
- Make asynchronous socket connection.

## Usage:
Check your python version.

Requires python 3+

```python
pip install -r requirements.txt
```


```python
from bpb import BreakingProxy

proxy = "http://username:password@proxyserver.net:port"
url = "www.example.com"

breaking_proxy = BreakingProxy(remote_host=url, proxy_url=proxy)
response = breaking_proxy.connect('GET')
response.data
```

#### Proxyserver

Using proxy server.
**Starting the proxy server**

```python
from proxyserver import TCPConnection


# localhost
host = "127.0.0.1"
port = 8080

server = TCPConnection(host=host, port=port)
server.start()
```
That's it. Your proxy server is running.
You can use this simple proxy server to test & Develope BreakingProxy