from sendbox_core.integrations.falcon_integration.headless_falcon_restful import BaseResource

from App.schemas import *
from bson import ObjectId


class InvoiceResource(BaseResource):
    """"""
    serializers = {
        "default": InvoiceRequestSchema,
        "response": InvoiceResponseSchema
    }

    def save(self, data, user_context, req, entity_context=None, id_context=None, **kwargs):
        """

        """
        user_id = user_context.get("user_id")
        return self.service_class.register(user_id=user_id, **data)

    def fetch(self, obj_id, user_context, req, entity_context=None, id_context=None, **kwargs):
        """

        :param obj_id:
        :type obj_id:
        :param user_context:
        :type user_context:
        :param req:
        :type req:
        :param entity_context:
        :type entity_context:
        :param id_context:
        :type id_context:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        if not ObjectId.is_valid(obj_id):
            return self.service_class.objects.get({"code": obj_id.strip()})
        return self.service_class.get(obj_id)


class InvoiceChargeResource(BaseResource):
    """"""
    serializers = {
        "default": GetChargeSchema,
        "response": InvoiceChargeSchema
    }

    def save(self, data, user_context, req, entity_context=None, id_context=None, **kwargs):
        """

        """
        user_id = user_context.get("user_id")
        return self.service_class.validate_invoice(user_id=user_id, **data)

    def on_get(self, req, res, entity_id=None, obj_id=None, resource_name=None):
        raise
