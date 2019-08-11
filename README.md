# Breaking Proxy
Making request beyond proxy.

## About:

HTTP Request througth proxy server.

A simple functional example of HTTP request over proxy server.

### TODO:
- Handles Response data & getting all bytes
- Get response as json
- Make asynchronous socket connection.

## Installation:

Check your python version.

```python
pip install -r requirements.txt
```


```python
from bpb import BreakingProxy

proxy = "http://username:password@proxyserver.net:port"
url = "www.example.com"

breaking_proxy = BreakingProxy(remote_host=url, proxy_url=proxy)
response = breaking_proxy.connect('GET')
response.status
response.data
```
