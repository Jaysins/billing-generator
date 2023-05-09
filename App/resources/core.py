from sendbox_core.integrations.falcon_integration.headless_falcon_restful import BaseResource

from App.schemas import *

core_serializers = {
    "default": CoreSchema,
    "response": CoreSchema
}


class CoreResource(BaseResource):
    """"""

    def limit_query(self, query, **kwargs):
        """"""
        return query


class SupportedCurrencyResource(BaseResource):
    """

    """
    serializers = {
        "response": SupportedCurrencySchema
    }

    def limit_query(self, query, **kwargs):
        """"""
        return query
