# HTTP proxy server


## About:

HTTP Proxy server is a proxy server module writting in python . 

## Requirements:

Check the requirements.txt file.

## Installation:

Check your python version.

```python
pip install -r requirements.tx
```


```python
from socketproxy import Socketproxy

proxy = "http://username:password@proxyserver.net:port"
url = "www.example.com"

s = Socketproxy(proxy, url)
s.connect('GET')
```
