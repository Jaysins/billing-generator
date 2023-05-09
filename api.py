import falcon

from App.custom.helpers import JsonHandler, TextHandler
# from App.resources.{core} import CoreResource, core_serializers, TopupOptionResource
# from App.services.{core} import *
from wsgiref import simple_server
from App import redis
from sendbox_core.integrations.falcon_integration.utils import register_api
from sendbox_core.integrations.falcon_integration.headless_falcon_middleware import *

from App.resources.core import CoreResource, core_serializers, SupportedCurrencyResource
from App.services.core import *
from App.custom.restful import *
from App.services.invoice import *
from App.resources.invoice import *

ignore = ["public_invoice", "supported_currencies"]

# Launching application
app = falcon.App(middleware=[AuthenticateMiddleware(ignored_endpoints=ignore, settings=settings, key_store=redis),
                             RequestResponseMiddleware(service="server", settings=settings),
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

supported_currency = SupportedCurrencyResource(SupportedCurrencyService, SupportedCurrencyResource.serializers,
                                               default_page_limit=1000)

invoice = InvoiceResource(InvoiceService, InvoiceResource.serializers)
public_invoice = InvoiceResource(InvoiceService, InvoiceResource.serializers)
invoice_charge = InvoiceChargeResource(InvoiceService, InvoiceChargeResource.serializers)

register_api(app, invoice, '/invoices', '/invoices/{obj_id}', '/invoices/{obj_id}/{resource_name}',
             prefix=settings.API_BASE)
register_api(app, supported_currency, '/supported_currencies', '/supported_currencies/{obj_id}',
             '/supported_currencies/{obj_id}/{resource_name}',
             prefix=settings.API_BASE)

register_api(app, public_invoice, '/public_invoice/{obj_id}', '/public_invoice/{obj_id}/{resource_name}',
             prefix=settings.API_BASE)

register_api(app, invoice_charge, '/invoice_charges', prefix=settings.API_BASE)

# use in development mode
if __name__ == "__main__":
    # httpd = simple_server.make_server('192.168.0.104', 8000, app)
    httpd = simple_server.make_server('127.0.0.1', 8000, app)
    httpd.serve_forever()
