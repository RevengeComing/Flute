# Flute
High Performance Web framework written in asyncio/uvloop/httptools

If you know how to work with flask micro-framework you know how to work with flute. its api is inspired by legendary flask. I must say its a clone of flask on top of asyncio protocol and httptools for http parsing and uvloop for making it high speed.

## Installation
its in pypi:
```
pip install flute
```

## Example:
just how you use flask:

```
from flute import Flute

app = Flute()

@app.route('/')
def index():
	return b"This is index page"

@app.route('/hello/<name>/')
def hello(name):
	resp = "Hello, {name}".format(name=name)
	return resp.encode()

app.run()
```
