import re
from pprint import pprint

import phonenumbers
from marshmallow import Schema, fields as _fields, validates, ValidationError, validate, \
    post_load, pre_load, post_dump, EXCLUDE
from marshmallow.decorators import validates_schema
from sendbox_core.base.utils import generate_random_code
from App.models import *


class ZeroAmountValidator(validate.Validator):

    def __call__(self, value):
        if not value:
            raise ValidationError("Minimum amount is NGN1", field_names=['amount'])
        if value <= 0:
            raise ValidationError("Minimum amount is NGN1", field_names=['amount'])


class RoundedFloat(_fields.Float):

    def __init__(self, places=None, **kwargs):
        self.places = places if places else 2
        super(RoundedFloat, self).__init__(**kwargs)

    def _format_num(self, value):
        if value is None:
            return None

        num = round(self.num_type(value), self.places)
        return num


def phone_number_validator(phone, country_code="NG"):
    """ Custom phone number validator to check that all phone numbers are unique and available """

    try:
        parsed_phone = phonenumbers.parse(phone, country_code)
        if not phonenumbers.is_valid_number(parsed_phone):
            return None
        phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.phonenumberutil.NumberParseException:
        return None
    return phone


class CoreSchema(Schema):
    code = _fields.String(required=True, allow_none=False)
    pk = _fields.String()
    name = _fields.String(required=True, allow_none=False)
    description = _fields.String(required=False, allow_none=True)
    last_updated = _fields.Date(required=False, allow_none=True)


class ExcludeSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class CustomerSchema(ExcludeSchema):
    email = _fields.Email(required=False, allow_none=True)
    name = _fields.String(required=False, allow_none=True)
    first_name = _fields.String(required=False, allow_none=True)
    last_name = _fields.String(required=False, allow_none=True)
    phone = _fields.String(required=False, allow_none=True)
    street = _fields.String(required=False, allow_none=True)
    street_line_2 = _fields.String(required=False, allow_none=True)
    state = _fields.String(required=False, allow_none=True)
    country = _fields.String(required=False, allow_none=True)
    lat = _fields.Float(required=False, allow_none=True)
    city = _fields.String(required=False, allow_none=True)
    post_code = _fields.String(required=False, allow_none=True)
    lng = _fields.Float(required=False, allow_none=True)


class ItemSchema(ExcludeSchema):
    sku = _fields.String(required=False, allow_none=True)
    quantity = _fields.Integer(required=True, allow_none=False)
    description = _fields.String(required=True, allow_none=False)
    category = _fields.String(required=False, allow_none=True)
    amount = _fields.Float(required=True, allow_none=False)
    weight = _fields.Float(required=False, allow_none=True)


class InvoiceResponseSchema(ExcludeSchema):
    """
    """

    pk = _fields.String(required=False, allow_none=False)
    _id = _fields.String(required=False, allow_none=False)
    code = _fields.String(required=False, allow_none=False)
    reference_code = _fields.String(required=False, allow_none=True)
    customer = _fields.Nested(CustomerSchema, required=False, allow_none=True)
    items = _fields.Nested(ItemSchema, required=False, allow_none=True, many=True)
    merchant = _fields.Dict(required=False, allow_none=True)
    payment_data = _fields.Dict(required=False, allow_none=True)
    date_paid = _fields.Date(required=False, allow_none=True)
    instance_id = _fields.String(required=True, allow_none=False)
    region = _fields.String(required=False, allow_none=True)
    status = _fields.Nested(CoreSchema, required=False, allow_none=True)
    payment_source_code = _fields.String(allow_none=True)
    user_id = _fields.String(required=False, allow_none=True)
    discount = _fields.Float(required=False, allow_none=True)
    currency = _fields.Nested(CoreSchema, required=False, allow_none=True)
    delivery_fee = _fields.Float(required=False, allow_none=True)
    extra_data = _fields.Dict(required=False, allow_none=True)
    sub_total = _fields.Float(required=False, allow_none=True)
    total = _fields.Float(required=False, allow_none=True)
    vat = _fields.Float(required=False, allow_none=True)
    auto_approve = _fields.Boolean(required=False, allow_none=True)
    notify_customer = _fields.Boolean(required=False, allow_none=True)
    vat_inclusive = _fields.Boolean(required=False, allow_none=True)
    amount_paid = _fields.Float(required=False, allow_none=True)
    url = _fields.String(required=False, allow_none=True)
    fx_rate = _fields.Float(required=False, allow_none=True)
    transaction_charge_rate = _fields.Float(required=False, allow_none=True)
    transaction_charge_cap = _fields.Float(required=False, allow_none=True)
    fx_amount_receivable = _fields.Float(required=False, allow_none=True)
    local_currency = _fields.String(required=False, allow_none=True)
    amount_receivable = _fields.Float(required=False, allow_none=True)
    transaction_charge = _fields.Float(required=False, allow_none=True)
    date_created = _fields.DateTime(required=False, allow_none=True)
    last_updated = _fields.DateTime(required=False, allow_none=True)


class InvoiceRequestSchema(InvoiceResponseSchema):
    """

    """
    customer = _fields.Nested(CustomerSchema, required=True, allow_none=False)
    currency = _fields.String(allow_none=True)

    @validates("currency")
    def validate_currency(self, val, **kwargs):
        """

        """
        if not SupportedCurrency.objects.raw({"code": val, "enabled": True}).count():
            raise ValidationError(message="Invalid Currency")


class SupportedCurrencySchema(ExcludeSchema):
    """

    """
    instance_id = _fields.String(required=False, allow_none=True)
    region = _fields.String(required=False, allow_none=True)
    code = _fields.String(required=True)
    name = _fields.String(required=False, allow_none=True)
    enabled = _fields.Boolean(default=False)
    symbol = _fields.String(required=False, allow_none=True)
    rates = _fields.List(_fields.Dict(required=False, allow_none=True), required=False, allow_none=True)


class RestConnectorSchema(ExcludeSchema):
    """
    Schema for rest connector
    """

    request_data = _fields.Raw(required=False, allow_none=True)
    response_data = _fields.Dict(required=False, allow_none=True)


class InstanceRequestSchema(ExcludeSchema):
    name = _fields.String(required=True, allow_none=False)
    pk = _fields.String(required=True, allow_none=False)
    description = _fields.String(required=False, allow_none=True)
    email = _fields.String(required=False, allow_none=True)
    phone = _fields.String(required=False, allow_none=True)
    type = _fields.String(required=False, allow_none=True)
    domain = _fields.String(required=False, allow_none=True)
    user_id = _fields.String(required=False, allow_none=True)


class RegionRequestSchema(ExcludeSchema):
    name = _fields.String(required=False, allow_none=True)
    code = _fields.String(required=False, allow_none=True)
    instance_id = _fields.String(required=False, allow_none=True)
    default = _fields.Boolean(required=False, allow_none=True)
    country = _fields.String(required=False, allow_none=True)
    currency = _fields.String(required=False, allow_none=True)
    international_currency = _fields.String(required=False, allow_none=True)

    @validates_schema
    def validate_schema(self, data, **kwargs):
        """

        @param data:
        @param kwargs:
        @return:
        """
        if Region.objects.raw({"code": data.get("code"), "instance_id": data.get("instance_id"),
                               "default": data.get("default")}).count():
            raise ValidationError(message="Region Already exists")


class ValidateShipmentPaymentSchema(Schema):
    """

    """
    txref = _fields.String(required=True, allow_none=False)
    reference_code = _fields.String(required=True, allow_none=False)
    status = _fields.Nested(CoreSchema, required=True, allow_none=False)
    user_id = _fields.String(required=True, allow_none=False)


class ProfileRequestSchema(Schema):
    email = _fields.String(required=False, allow_none=True)
    name = _fields.String(required=False, allow_none=True)
    first_name = _fields.String(required=False, allow_none=True)
    last_name = _fields.String(required=False, allow_none=True)
    username = _fields.String(required=False, allow_none=True)
    phone = _fields.String(required=False, allow_none=True)
    instance_id = _fields.String(required=True, allow_none=False)
    is_anonymous = _fields.Boolean(required=False, allow_none=True)
    entity_id = _fields.String(required=False, allow_none=True)
    user_id = _fields.String(required=False, allow_none=True)
    profile_type = _fields.String(required=False, allow_none=False)
    account_type = _fields.String(required=False, allow_none=True)
    referral_code = _fields.String(required=False, allow_none=True)
    referred_by = _fields.String(required=False, allow_none=True)
    currency = _fields.String(required=False, allow_none=True)
    region = _fields.String(required=False, allow_none=True)

    @validates_schema
    def validate_schema(self, data, **kwargs):
        """

        @param data:
        @param kwargs:
        @return:
        """
        if Profile.objects.raw({"instance_id": data.get("instance_id"), "user_id": data.get("user_id"),
                                "entity_id": data.get("user_id")}).count():
            raise ValidationError(message="Profile Already exists")


class ProfileUpdateSchema(Schema):
    email = _fields.String(required=False, allow_none=True)
    name = _fields.String(required=False, allow_none=True)
    phone = _fields.String(required=False, allow_none=True)
    id = _fields.String(required=False, allow_none=True)
    user_id = _fields.String(required=False, allow_none=True)
    is_anonymous = _fields.Boolean(allow_none=True)
    instance_id = _fields.String(required=True, allow_none=False)
    entity_id = _fields.String(allow_none=False)
    country = _fields.String(allow_none=False)
    profile_type = _fields.String(allow_none=False)

    @post_load
    def prepare_payload(self, data, **kwargs):
        """

        @param data:
        @type data:
        @param kwargs:
        @type kwargs:
        @return:
        @rtype:
        """
        return {key: value for key, value in data.items() if value}


class EmbeddedAddressSchema(ExcludeSchema):
    street = _fields.String(required=False, allow_none=True)
    street_line_2 = _fields.String(required=False, allow_none=True)
    city = _fields.String(required=True, allow_none=False)
    state = _fields.String(required=False, allow_none=True)
    country = _fields.String(required=True, allow_none=False)
    lat = _fields.String(required=False, allow_none=True)
    lng = _fields.String(required=False, allow_none=True)
    post_code = _fields.String(required=False, allow_none=True)


class EntityRequestSchema(ExcludeSchema):
    """
    Model for Status
    """
    name = _fields.String(required=True, allow_none=False)
    entity_id = _fields.String(required=True, allow_none=False)
    email = _fields.String(required=False, allow_none=True)
    phone = _fields.String(required=False, allow_none=True)
    currency = _fields.String(required=False, allow_none=True)
    description = _fields.String(required=False, allow_none=True)
    user_id = _fields.String(required=False, allow_none=True)
    region = _fields.String(required=False, allow_none=True)
    type = _fields.String(required=False, allow_none=False)
    address = _fields.Nested(EmbeddedAddressSchema, required=False, allow_none=False)
    # instance_id = _fields.String(required=True, allow_none=False)
    category = _fields.String(allow_none=True)
    logo = _fields.String(allow_none=True)
    enabled = _fields.Boolean(required=False, allow_none=True)


class GetChargeSchema(ExcludeSchema):
    local_currency = _fields.String(required=False, allow_none=True)
    instance_id = _fields.String(required=False, allow_none=True)
    currency = _fields.String(required=True, allow_none=False)
    amount = _fields.Float(required=True, allow_none=False)


class InvoiceChargeSchema(ExcludeSchema):
    fx_rate = _fields.Float(required=False, allow_none=True)
    amount = _fields.Float(required=False, allow_none=True)
    fx_amount_receivable = _fields.Float(required=False, allow_none=True)
    local_currency = _fields.String(required=False, allow_none=True)
    currency = _fields.String(required=False, allow_none=True)
    amount_receivable = _fields.Float(required=False, allow_none=True)
    transaction_charge_cap = _fields.Float(required=False, allow_none=True)
    transaction_charge_rate = _fields.Float(required=False, allow_none=True)
    transaction_charge = _fields.Float(required=False, allow_none=True)
