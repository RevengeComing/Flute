import asyncio
import uvloop

from protocol import FluteHttpProtocol
from routing import RouteMap, Route, create_endpoint, create_error_response
from statics import HTTP_STATUS_CODES, HTTP_ERRORS

class Flute(object):

    routes = RouteMap()
    _error_handlers = {}

    def __init__(self):
        # self._set_default_error_handlers()
        pass

    # def _set_default_error_handlers(self):
    #     for error_number, desc in HTTP_ERRORS.items():
    #         self._error_handlers[error_number] = create_error_response(error_number, desc)

    def run_app(self, host="127.0.0.1", port=5000):
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        loop = asyncio.get_event_loop()
        coro = loop.create_server(lambda: FluteHttpProtocol(self), host, port)
        loop.run_until_complete(coro)
        try:
            print('*** You can access Flute Server @ http://%s:%d ***' % (host, port))
            loop.run_forever()
        except KeyboardInterrupt:
            print("Server is Closing")
        loop.close()

    def add_url_rule(self, path, endpoint=None, view_function=None, **options):
        if endpoint is None:
            endpoint = create_endpoint(view_function)

        methods = options.pop('methods', None)
        if methods is None:
            methods = ['GET',]

        route = Route(path, endpoint, view_function, methods=methods, **options)
        self.routes.add(route)

    def route(self, path, **options):
        def decorator(view_function):
            endpoint = options.pop('endpoint', None)
            self.add_url_rule(path, endpoint, view_function, **options)
            return view_function
        return decorator

    def errorhandler(self, code_or_exception):        
        def decorator(view_function):
            self._register_error_handler(code_or_exception, view_function)
            return view_function
        return decorator

    def _register_error_handler(self, code, view_function):
        self._error_handlers[code] = view_function

    async def get_error_response(self, code, connection):
        func = self._error_handlers.get(code)
        if func: return await func(connection)
        else: return create_error_response(code, HTTP_ERRORS[code])



def test():
    app = Flute()

    @app.route('/')
    async def index(connection):
        return b"test"

    @app.errorhandler(404)
    async def index(connection):
        return b"nisesh"

    app.run_app()


if __name__ == "__main__":
    test()