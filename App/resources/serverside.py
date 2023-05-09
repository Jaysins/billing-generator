import json

import falcon
from pymodm import MongoModel
from pyotp import TOTP
from sendbox_core.integrations.falcon_integration.errors import ValidationFailed
from sendbox_core.integrations.falcon_integration.headless_falcon_restful import BaseResource

import settings
from App.schemas import *


def validate(schema, data_):
    """
    prepares the response object with the specified schema
    :param req: the falcon request object
    :param schema: the schema class that should be used to validate the response
    :return: falcon.Response
    """
    print(data_, "skybison")
    req_data = data_
    try:
        data = schema().load(data=req_data)
    except ValidationError as e:
        raise falcon.HTTPError(status="409 ", title=str(e), description=str(e))

    return data


def marshal(resp, schema):
    """
    prepares the response object with the specified schema
    :param resp: the falcon response object
    :param schema: the schema class that should be used to validate the response
    :return: falcon.Response
    """
    data = resp
    resp_ = None
    # print(data, type(data))
    if isinstance(data, list):
        resp_ = []
        for d in data:
            resp_.append(schema().dump(d).data)
        # resp.media = resp_
    if isinstance(data, dict):
        resp_ = schema().load(
            data=data
        ).data

    if isinstance(data, MongoModel):
        resp_ = schema().dump(
            data
        ).data
    return resp_


class BackendResource(BaseResource):
    """"""
    serializers = {
        "default": RestConnectorSchema,
        "response": RestConnectorSchema
    }

    def register_profile(self, data, user_context, req, **kwargs):
        """

        @param data:
        @param user_context:
        @param req:
        @param kwargs:
        @return:
        """
        request_data = data.get("request_data")
        try:
            pprint(request_data)
            validated_data = ProfileRequestSchema().load(data=request_data, unknown=EXCLUDE)
        except ValidationError as e:
            raise falcon.HTTPError(status="409 ", title=str(e), description=str(e))

        request_data.update(**validated_data)

        print("the req===")
        # request_data.update(**request_data.get("user"))
        pprint(request_data)
        res = self.service_class.profile_service.register(**request_data)
        return dict(response_data=res.to_dict(do_dump=True))

    def register_entity(self, data, user_context, req, **kwargs):
        """

        @param data:
        @param user_context:
        @param req:
        @param kwargs:
        @return:
        """
        request_data = data.get("request_data")
        try:
            pprint(request_data)
            validated_data = EntityRequestSchema().load(data=request_data, unknown=EXCLUDE)
        except ValidationError as e:
            raise falcon.HTTPError(status="409 ", title=str(e), description=str(e))

        request_data.update(**validated_data)

        print("the req===")
        # request_data.update(**request_data.get("user"))
        pprint(request_data)
        res = self.service_class.entity_service.register(**request_data)
        return dict(response_data=res.to_dict(do_dump=True))

    def update_profile(self, data, user_context, req, **kwargs):
        """

        """
        request_data = data.get("request_data")
        try:
            pprint(request_data)
            validated_data = ProfileUpdateSchema().load(data=request_data, unknown=EXCLUDE)
        except ValidationError as e:
            raise falcon.HTTPError(status="409 ", title=str(e), description=str(e))
        request_data.update(**validated_data)
        us = self.service_class.profile_service.find_one({"user_id": request_data.get("user_id")})
        if us:
            res = self.service_class.profile_service.update(us.pk, **request_data)
            return dict(response_data=res.to_dict(do_dump=True))
        return dict(response_data=dict(status="failed"))

    def register_instance(self, data, user_context, req, **kwargs):
        """

        @param data:
        @param user_context:
        @param req:
        @param kwargs:
        @return:
        """
        request_data = data.get("request_data")
        try:
            validated_data = InstanceRequestSchema().load(data=request_data)
        except ValidationError as e:
            raise falcon.HTTPError(status="409 ", title=str(e), description=str(e))

        request_data.update(**validated_data)
        res = self.service_class.instance_service.register(**request_data)
        return dict(response_data=res.to_dict(do_dump=True))

    def register_region(self, data, user_context, req, **kwargs):
        """

        @param data:
        @param user_context:
        @param req:
        @param kwargs:
        @return:
        """
        request_data = data.get("request_data")
        try:
            validated_data = RegionRequestSchema().load(data=request_data)
        except ValidationError as e:
            raise falcon.HTTPError(status="409 ", title=str(e), description=str(e))

        request_data.update(**validated_data)
        res = self.service_class.region_service.register(**request_data)
        return dict(response_data=res.to_dict(do_dump=True))

    def validate_invoice_payment(self, data, user_context, req, **kwargs):
        """

        @param data:
        @param user_context:
        @param req:
        @param kwargs:
        @return:

        """
        request_data = data.get("request_data")

        print(request_data, "borhhhh")
        try:
            validated_data = ValidateShipmentPaymentSchema().load(data=request_data, unknown=EXCLUDE)
        except ValidationError as e:
            raise falcon.HTTPError(status="409 ", title=str(e), description=str(e))

        request_data.update(**validated_data)
        res = self.service_class.invoice_service.validate_invoice_payment(**request_data)
        return dict(response_data=res.to_dict(do_dump=True))
