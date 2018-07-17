# proxy

Web proxy-server in Python

Handles multiple clients asynchronously.

`Client--->proxy--->Server`

# Socketproxy

Connect through socket with proxy

Usage:

```python
from socketproxy import Socketproxy

proxy = "http://username:password@proxyserver.net:port"
url = "www.example.com"

s = Socketproxy(proxy, url)
s.connect('GET')
```
