import asyncio
from logging import Logger, DEBUG
import datetime

from httptools import HttpRequestParser, parse_url
from werkzeug.routing import NotFound, RequestRedirect, MethodNotAllowed

from statics import HTTP_STATUS_CODES

__all__ = ['FluteHttpProtocol']


class Response(object):
    __slots__ = ['headers', 'body', 'cookies']

    def __init__(self, headers, body, **options):
        self.headers = headers
        self.body = body

    def add_cookie(self, key, value):
        self.cookies[key] = value

    def get_text(self):
        header = "\r\n".join("{0}: {1}".format(key, value) for key, value in self.headers) + "\r\n\r\n"
        text = header + body
        return text.encode()


class FluteHttpProtocol(asyncio.Protocol):

    headers = dict()

    resp_headers = {}

    def __init__(self, app):
        self.app = app

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        hrp = HttpRequestParser(self)
        hrp.feed_data(data)
        self.http_version = hrp.get_http_version()
        self.method = hrp.get_method()
        before_requests = asyncio.async(self.call_before_requests())
    
    async def call_before_requests(self):
        await self.call_handler()

    async def call_handler(self):
        # adapter = self.app.create_url_adapter()
        try:
            match = self.app.adapter.match(self.url_requested.path.decode('utf-8'))

            # print(match)
            func = self.app.view_functions.get(match[0])
            # print(func)
            resp = await func(self, **match[1])
            # if not route:
            #     self.status_code = 404
            #     self.create_response_header()
            #     resp = await self.app.get_error_response(404, self)
            #     self.transport.write(self.header + resp)
            #     self.transport.close()
            # else:
            self.status_code = 200
            self.create_response_header()
            self.transport.write(self.header + resp)
            self.transport.close()


            # print('[{datetime}] : {status_code} {method} {url}'.format(datetime=datetime.datetime.now(),
            #                                                            status_code=self.status_code,
            #                                                            method=self.method.decode('utf-8'),
            #                                                            url=self.url_requested.path.decode('utf-8')))
        except NotFound:
            pass
        except MethodNotAllowed:
            pass
        except RequestRedirect as e:
            print(e)
        finally:
            await self.call_after_requests()
    
    async def call_after_requests(self):
        pass  

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

    # def on_headers_complete(self):
    #     pass

    def on_body(self, body):
        self.req_body = body

    # def on_message_complete(self):
    #     pass

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