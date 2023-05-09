import falcon
from App import *
from sendbox_core.integrations.falcon_integration.headless_falcon_middleware import AuthenticateMiddleware, \
    RequestResponseMiddleware, QueryParamsMiddleware

from App.custom.helpers import JsonHandler, TextHandler
from App.custom.restful import *
from sendbox_core.integrations.falcon_integration.utils import register_api
from wsgiref import simple_server
from App.resources.invoice import InvoiceResource
from App.services.invoice import InvoiceService

ignore = []

# Launching application
app = falcon.App(middleware=[AuthenticateMiddleware(ignored_endpoints=ignore, settings=settings, key_store=redis,
                                                    admin=True),
                             RequestResponseMiddleware(service=settings.JWT_AUDIENCE_CLAIM, settings=settings),
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

invoice = InvoiceResource(InvoiceService, InvoiceResource.serializers, permit=admin_permit, limiter=admin_query)

register_api(app, invoice, '/invoices', "/invoices/{obj_id}", "/invoices/{obj_id}/{resource_name}",
             prefix=settings.API_BASE)

# use in development mode
if __name__ == "__main__":
    # httpd = simple_server.make_server('192.168.0.104', 8000, app)
    httpd = simple_server.make_server('127.0.0.1', 5100, app)
    httpd.serve_forever()
