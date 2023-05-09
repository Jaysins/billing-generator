import falcon
from sendbox_core.integrations.falcon_integration.headless_falcon_middleware import AuthenticateMiddleware, \
    RequestResponseMiddleware, QueryParamsMiddleware

from App.custom.helpers import JsonHandler, TextHandler
from App.custom.middleware import *
from wsgiref import simple_server
import settings
from App import redis
from sendbox_core.integrations.falcon_integration.utils import register_api
from App.resources.serverside import BackendResource
from App.services.serverside import InvoicingBackendService

ignore = ['engine']

# Launching application
app = falcon.App(middleware=[AuthenticateMiddleware(ignored_endpoints=ignore, settings=settings, key_store=redis),
                             RequestResponseMiddleware(domain="internal", settings=settings),
                             QueryParamsMiddleware()])

custom_handlers = {
    'application/json': JsonHandler(),
    'application/json; charset=UTF-8': JsonHandler(),
    'text/plain': TextHandler(),
    '*/*': TextHandler(),
}

# error handling block
# app.add_error_handler(ObjectNotFoundException, ObjectNotFoundError.handler)
# app.add_error_handler(TypeError, MissingArgumentError.handler)
# app.add_error_handler(MissingArgumentException, MissingArgumentError.handler)
# app.add_error_handler(ActionFailedException, ActionFailedError.handler)

# specifying custom json handlers to avoid "NOT JSON SERIALIZABLE ISSUES"
app.req_options.media_handlers.update(custom_handlers)
app.resp_options.media_handlers.update(custom_handlers)

engine = BackendResource(InvoicingBackendService, BackendResource.serializers)


register_api(app, engine, '/engine', '/engine/{resource_name}', prefix=settings.API_BASE)  # post

# use in development mode
if __name__ == "__main__":
    # httpd = simple_server.make_server('192.168.0.104', 8000, app)
    httpd = simple_server.make_server('127.0.0.1', 7500, app)
    httpd.serve_forever()
