import asyncio
import uvloop

from werkzeug.routing import Map, Rule, NotFound, RequestRedirect
from werkzeug.exceptions import HTTPException, InternalServerError, \
     MethodNotAllowed, BadRequest, default_exceptions

from protocol import FluteHttpProtocol
from utils import _endpoint_from_view_func
from statics import HTTP_STATUS_CODES, HTTP_ERRORS

class Flute(object):

    url_rule_class = Rule
    _error_handlers = {}

    config = {
        'SERVER_NAME':'localhost',
        'APPLICATION_ROOT':None,
        'PREFERRED_URL_SCHEME':None,
    }

    def __init__(self):
        self.url_map = Map()
        self.view_functions = {}

        self._error_handlers = {}
        self.error_handler_spec = {None: self._error_handlers}

    # def _set_default_error_handlers(self):
    #     for error_number, desc in HTTP_ERRORS.items():
    #         self._error_handlers[error_number] = create_error_response(error_number, desc)

    def add_url_rule(self, rule, endpoint=None, view_function=None, **options):
        """ Flask's add_url_rule """
        if endpoint is None:
            endpoint = _endpoint_from_view_func(view_function)
        options['endpoint'] = endpoint

        methods = options.pop('methods', None)
        if methods is None:
            methods = getattr(view_function, 'methods', None) or ('GET',)
        if isinstance(methods, str):
            raise TypeError('Allowed methods have to be iterables of strings, '
                            'for example: @app.route(..., methods=["POST"])')
        methods = set(item.upper() for item in methods)

        required_methods = set(getattr(view_function, 'required_methods', ()))

        provide_automatic_options = getattr(view_function,
            'provide_automatic_options', None)

        if provide_automatic_options is None:
            if 'OPTIONS' not in methods:
                provide_automatic_options = True
                required_methods.add('OPTIONS')
            else:
                provide_automatic_options = False

        methods |= required_methods

        rule = self.url_rule_class(rule, methods=methods, **options)
        rule.provide_automatic_options = provide_automatic_options

        self.url_map.add(rule)
        if view_function is not None:
            old_func = self.view_functions.get(endpoint)
            if old_func is not None and old_func != view_function:
                raise AssertionError('View function mapping is overwriting an '
                                     'existing endpoint function: %s' % endpoint)
            self.view_functions[endpoint] = view_function

    def route(self, rule, **options):
        def decorator(view_function):
            endpoint = options.pop('endpoint', None)
            self.add_url_rule(rule, endpoint, view_function, **options)
            return view_function
        return decorator

    def create_url_adapter(self):
        return self.url_map.bind(
            self.config['SERVER_NAME'],
            script_name=self.config['APPLICATION_ROOT'] or '/',
            url_scheme=self.config['PREFERRED_URL_SCHEME'])

    def _get_exc_class_and_code(self, exc_class_or_code):
        """Ensure that we register only exceptions as handler keys"""
        if isinstance(exc_class_or_code, int):
            exc_class = default_exceptions[exc_class_or_code]
        else:
            exc_class = exc_class_or_code

        assert issubclass(exc_class, Exception)

        if issubclass(exc_class, HTTPException):
            return exc_class, exc_class.code
        else:
            return exc_class, None

    def errorhandler(self, code_or_exception):
        def decorator(f):
            self._register_error_handler(None, code_or_exception, f)
            return f
        return decorator

    def _register_error_handler(self, key, code_or_exception, view_function):
        if isinstance(code_or_exception, HTTPException):
            raise ValueError(
                'Tried to register a handler for an exception instance {0!r}. '
                'Handlers can only be registered for exception classes or HTTP error codes.'
                .format(code_or_exception))

        exc_class, code = self._get_exc_class_and_code(code_or_exception)

        handlers = self.error_handler_spec.setdefault(key, {}).setdefault(code, {})
        handlers[exc_class] = view_function

    async def get_error_response(self, code, connection):
        func = self._error_handlers.get(code)
        if func: return await func(connection)
        else: return create_error_response(code, HTTP_ERRORS[code])

    def run(self, host="127.0.0.1", port=5000):
        self.adapter = self.create_url_adapter()
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



if __name__ == "__main__":
    
    def test():
        app = Flute()

        @app.route('/')
        async def index(connection):
            return b"test"

        @app.route('/hello/<name>/')
        async def index2(connection, name):
            response = "Hello, %s" % name
            return response.encode()

        @app.errorhandler(404)
        async def index(connection):
            return b"nisesh"

        app.run()

    test()