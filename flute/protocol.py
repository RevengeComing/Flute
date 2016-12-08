import asyncio
from logging import Logger, DEBUG
import datetime

from httptools import HttpRequestParser, parse_url

from statics import HTTP_STATUS_CODES

__all__ = ['FluteHttpProtocol']

RESPONSE1_HEAD = b'''
HTTP/1.0 200 OK
Date: Sun, 10 Oct 2010 23:26:07 GMT
Server: Apache/2.2.8 (Ubuntu) mod_ssl/2.2.8 OpenSSL/0.9.8g
Accept-Ranges: bytes
Content-Length: 41
Connection: close
Content-Type: text/html

<html><body><h1>asdasd</h1></body></html>
'''


class FluteHttpProtocol(asyncio.Protocol):

    headers = dict()

    def __init__(self, app):
        self.app = app

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        hrp = HttpRequestParser(self)
        hrp.feed_data(data)
        self.http_version = hrp.get_http_version()
        self.method = hrp.get_method()

        task = asyncio.async(self.call_handler()) # or asyncio.get_event_loop().create_task()
        # task.add_done_callback(self.handle_go_result)

    async def call_handler(self):
        route = self.app.routes.get_route(self.url_requested.path.decode('utf-8'))
        if not route:
            self.status_code = 404
            self.create_response_header()
            resp = await self.app.get_error_response(404, self)
            self.transport.write(self.header + resp)
            self.transport.close()
        else:
            resp = await route['func'](self)
            self.status_code = 200
            self.create_response_header()
            self.transport.write(self.header + resp)
            self.transport.close()
        print('[{datetime}] : {status_code} {method} {url}'.format(datetime=datetime.datetime.now(),
                                                                   status_code=self.status_code,
                                                                   method=self.method.decode('utf-8'),
                                                                   url=self.url_requested.path.decode('utf-8')))

    def create_response_header(self):
        self.header = "HTTP/%s %d %s\r\n" % (self.http_version, self.status_code, HTTP_STATUS_CODES[self.status_code])
        self.header += "Server: Flute Server 0.1.0\r\n"
        # self.header += "Content-Length: 41\r\n"
        self.header += "Connection: close\r\n"
        self.header += "Content-Type: text/html\r\n"

        self.header += "\r\n"
        self.header = self.header.encode()

    # def on_message_begin(self):
    #     pass

    def on_header(self, name, value):
        self.headers[name] = value

    def on_headers_complete(self):
        pass

    def on_body(self, body):
        req_body = body

    def on_message_complete(self):
        pass

    def on_url(self, url):
        self.url_requested = parse_url(url)

    # def on_chunk_header(self):
    #     pass

    # def on_chunk_complete(self):
    #     pass

def test():
    loop = asyncio.get_event_loop()
    coro = loop.create_server(lambda: FluteHttpProtocol(), '127.0.0.1', 5000)
    loop.run_until_complete(coro)

    loop.run_forever()
    loop.close()

if __name__ == "__main__":
    test()