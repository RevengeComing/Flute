import re


def create_endpoint(function):
    return function.__name__

def create_error_response(error_number, desc):
    response = """
    <html>
        <title>{desc}</title>
        <body>
            <h2>Error {error_number}<h2>
            <h3>{desc}<h3>
        </body>
    </html>
    """.format(desc=desc, error_number=error_number)
    return response.encode()


class RouteMap(object):

    endpoints = {}
    routes = {}

    def add(self, rule):
        self.routes[rule.path] = {
            'func':rule.view_function,
            'methods':rule.methods
        }
        self.endpoints[rule.endpoint] = rule.path

    def get_route(self, path):
        return self.routes.get(path)

    def get_path(self, endpoint):
        return self.endpoints.get(endpoint)


class Route(object):

    def __init__(self, path, endpoint, view_function, methods=None, **options):
        self.path = path
        self.endpoint = endpoint
        self.view_function = view_function
        self.methods = methods

    def get_variables(self):        
        return re.findall(r'\<([^]]*)\>',self.path)
