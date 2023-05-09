"""
models.py

Data model file for application. This will connect to the mongo database and provide a source for storage
for the application service

"""
import importlib
import inspect
from pprint import pprint

import pymongo
from bson import ObjectId, SON
from munch import munchify
from pymongo.write_concern import WriteConcern
from pymongo.operations import IndexModel
from pymodm import connect, fields, MongoModel, EmbeddedMongoModel
from datetime import datetime, timedelta

from sendbox_core.base.utils import convert_dict, roundUp
import json

import settings
from pymodm.common import _import

# Must always be run before any other database calls can follow
from App.custom.helpers import calculate_exchange_rate
from pymodm.context_managers import no_auto_dereference

connect(settings.DATABASE_URL, connect=False, maxPoolSize=None)


def get_obj_attr(obj, attr='name'):
    """get the code of a reference field object"""
    # print "getting obj atr"
    try:
        atr = getattr(obj, attr)
        if atr:
            return atr
        return obj
    except Exception as e:
        # print e
        return obj


class ReferenceField(fields.ReferenceField):
    """
    ReferenceField
    """

    def dereference_if_needed(self, value):
        """

        :param value:
        :type value:
        :return:
        :rtype:
        """

        if isinstance(value, self.related_model):
            return value
        if self.model._mongometa._auto_dereference:
            dereference_id = _import('pymodm.dereference.dereference_id')
            return dereference_id(self.related_model, value)
        value_stick = self.related_model._mongometa.pk.to_python(value)
        if not isinstance(value_stick, self.related_model):
            # print(type(value_stick))
            # value_stick = value_stick if value_stick and len(value_stick) > 10 else ObjectId(value_stick)
            check = self.related_model.objects.raw({"_id": value_stick})
            # print(check.count(), "dondnoenxe")
            if check.count() < 1:
                return self.related_model._mongometa.pk.to_python(value)
            return check.first()
        return self.related_model._mongometa.pk.to_python(value)


class AppMixin:
    """ App mixin will hold special methods and field parameters to map to all model classes"""

    def to_dict(self, exclude=None, do_dump=False):
        """

        @param exclude:
        @param do_dump:
        @return:
        """
        if isinstance(self, (MongoModel, EmbeddedMongoModel)):
            d = self.to_custom_son(exclude=exclude).to_dict()
            # [d.pop(i, None) for i in exclude]
            return json.loads(json.dumps(d, default=str)) if do_dump else d
        return self.__dict__

    def to_custom_son(self, exclude=None):
        """Get this Model back as a :class:`~bson.son.SON` object.

        :returns: SON representing this object as a MongoDB document.

        """
        son = SON()
        exclude = exclude if exclude else []
        with no_auto_dereference(self):
            for field in self._mongometa.get_fields():
                if field.is_undefined(self):
                    continue
                if exclude and field.attname in exclude:
                    continue
                value = self._data.get_python_value(field.attname, field.to_python)
                if field.is_blank(value):
                    son[field.mongo_name] = value
                else:
                    value = field.to_mongo(value)
                    if type(value) is list:
                        for i in value:
                            if isinstance(i, SON):
                                i.pop("_cls", None)
                                for ex in exclude:
                                    i.pop(ex, None)
                    if isinstance(value, SON):
                        value.pop("_cls", None)
                        for ex in exclude:
                            value.pop(ex, None)
                    # print(field.mongo_name)

                    # print(son[field.mongo_name])

                    son[field.mongo_name] = field.to_mongo(value)
        update_data = dict()
        if "pk" not in exclude and son.get("_id"):
            update_data.update(pk=str(son.get("_id")))
        if not son.get("code") and "code" not in exclude:
            update_data.update(code=son.get("_id"))
        son.update(**update_data)
        son.pop("_cls", None)

        return son

    def to_full_dict(self):
        """
        Retrieve all values of this model as a dictionary including values of methods that are
        wrapped with the @property decorator
        """
        data = inspect.getmembers(self)
        data_ = dict()
        for d in data:
            if not inspect.ismethod(d[1]) and '__' not in d[0] \
                    and type(d[1]) in [str, int, dict, list, float, datetime, ObjectId, bytes, tuple, bool] \
                    or isinstance(d[1], (MongoModel, EmbeddedMongoModel)):

                data_[d[0]] = d[1]
                if type(d[1]) == ObjectId:
                    data_[d[0]] = str(d[1])
                if isinstance(d[1], (MongoModel, EmbeddedMongoModel)) and getattr(d[1], 'to_son', None):
                    data_[d[0]] = d[1].to_son().to_dict()
                #     for k,v in data_[d[0]].items():
                #         print k, v, type(v)
                #         if type(v) == list:
                #             for c in v:
                #                 if isinstance(c, (MongoModel, EmbeddedMongoModel)):
                #                     data_[d[0]][k].append(c.to_son().to_dict())
                if type(d[1]) in [list, tuple] and len(d[1]) > 0:
                    sub = []
                    for i in d[1]:
                        if getattr(i, 'to_son', None):
                            sub.append(i.to_son().to_dict())
                    data_[d[0]] = sub
                    #     print (i)

        # pprint(data_)
        return data_

    def to_full_json(self):
        """
        Retrieve all values of this model as a dictionary including values of methods that are
        wrapped with the @property decorator
        """
        data_ = self.to_full_dict()
        # if data_.has_key("_defaults"):
        if "_defaults" in data_.keys():
            data_.pop("_defaults")
        data_ = convert_dict(data_)
        return data_

    @property
    def id(self):
        return str(self._id)

    def to_full_json_dict(self):
        """
        Retrieve all values of this model as a dictionary including values of methods that are
        wrapped with the @property decorator
        """
        data_ = self.to_full_dict()
        if data_.get("_defaults"):
            data_.pop("_defaults")
        data_ = convert_dict(data_)

        return json.loads(data_)


class Country(MongoModel, AppMixin):
    code = fields.CharField(primary_key=True)
    name = fields.CharField(required=True, blank=False)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)


class Currency(MongoModel, AppMixin):
    code = fields.CharField(primary_key=True)
    name = fields.CharField()
    symbol = fields.CharField()
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)


class Person(EmbeddedMongoModel):
    email = fields.CharField(required=False, blank=True)
    name = fields.CharField(required=False, blank=True)
    phone = fields.CharField(required=False, blank=True)
    user_id = fields.CharField(required=False, blank=True)

    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True

        indexes = [
            IndexModel([('email', pymongo.ASCENDING), ('email', pymongo.DESCENDING)]),
            IndexModel([('phone', pymongo.ASCENDING), ('phone', pymongo.DESCENDING)]),
            IndexModel([('name', pymongo.ASCENDING), ('name', pymongo.DESCENDING)])
        ]


class InvoicingConfiguration(MongoModel, AppMixin):
    region = fields.CharField(required=False, blank=True)
    country = fields.ReferenceField(Country, required=True, blank=False)
    currency = fields.ReferenceField(Currency, required=True, blank=False)
    instance_id = fields.CharField(required=False, blank=True)
    data = fields.DictField(required=False, blank=True)
    internal_data = fields.DictField(required=False, blank=True)
    vat_rate = fields.FloatField(required=False, blank=True)
    insurance_rate = fields.FloatField(required=False, blank=True)
    cargo_weight_limit = fields.FloatField(required=False, blank=True)
    base_pickup_fee = fields.FloatField(required=False, blank=True)
    web_base_url = fields.CharField(required=False, blank=True)
    incremental_pickup_fee = fields.FloatField(required=False, blank=True)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)


class Account(EmbeddedMongoModel):
    """"""

    key = fields.CharField(required=True, blank=False)
    type = fields.CharField(required=True, blank=False)
    currency = fields.CharField(required=False, blank=True)
    region = fields.CharField(required=False, blank=True)
    purpose = fields.CharField(required=False, blank=True)
    name = fields.CharField(required=False, blank=True)
    email = fields.CharField(required=False, blank=True)
    phone = fields.CharField(required=False, blank=True)
    is_main = fields.BooleanField(required=False, blank=True)
    is_anonymous = fields.BooleanField(required=False, blank=True)

    def __hash__(self):
        """ custom hashing method so that comparison will work on an object level """
        return hash((self.purpose, self.currency))

    def __eq__(self, other):
        """ custom equality function to ensure object can be compared using either a string or object value """

        # compare permission with another permission object
        if isinstance(other, Account):
            return hash((self.purpose, self.currency)) == other.__hash__()

        if isinstance(other, (str, bytes)):
            return self.purpose == other

        if isinstance(other, tuple):
            return (self.purpose, self.currency) == other


class Profile(MongoModel, AppMixin):
    """ Model for storing information about an entity or user who owns an account or set of accounts.
    _id will be equivalent to either the user_id or the entity_id
    """
    email = fields.CharField(required=False, blank=True)
    username = fields.CharField(required=False, blank=True)
    name = fields.CharField(required=False, blank=True)
    first_name = fields.CharField(required=False, blank=True)
    last_name = fields.CharField(required=False, blank=True)
    region = fields.CharField(required=False, blank=True)
    phone = fields.CharField(required=False, blank=True)
    instance_id = fields.CharField(required=True, blank=False)
    referral_code = fields.CharField(required=False, blank=True)
    referred_by = fields.CharField(required=False, blank=True)
    entity_id = fields.CharField(required=False, blank=True)
    profile_type = fields.CharField(required=False, blank=True)
    country = ReferenceField(Country, required=False, blank=True)
    is_anonymous = fields.BooleanField(required=False, blank=True)
    user_id = fields.CharField(required=True, blank=False)
    default_currency = ReferenceField(Currency, required=False, blank=True)
    accounts = fields.EmbeddedDocumentListField(Account, required=False, blank=True)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)

    def get_account(self, purpose, currency):
        """ Fetch profile from user """
        print("the purpepepe", self.user_id, purpose, currency)
        print((p for p in self.accounts if p == (purpose, currency)), None)
        return next((p for p in self.accounts if p == (purpose, currency)), None)

    def add_account(self, **kwargs):
        """
        Tem
        """
        account = Account(**kwargs)
        self.accounts.append(account)
        return self.save()


class InstanceAccount(EmbeddedMongoModel):
    """"""

    key = fields.CharField(required=True, blank=False)
    type = fields.CharField(required=True, blank=False)
    currency = fields.CharField(required=False, blank=True)
    region = fields.CharField(required=False, blank=True)
    purpose = fields.CharField(required=False, blank=True)
    name = fields.CharField(required=False, blank=True)
    email = fields.CharField(required=False, blank=True)
    phone = fields.CharField(required=False, blank=True)
    is_main = fields.BooleanField(required=False, blank=True)
    is_anonymous = fields.BooleanField(required=False, blank=True)

    def __hash__(self):
        """ custom hashing method so that comparison will work on an object level """
        return hash((self.purpose, self.currency, self.region))

    def __eq__(self, other):
        """ custom equality function to ensure object can be compared using either a string or object value """

        # compare permission with another permission object
        if isinstance(other, Account):
            return hash((self.purpose, self.currency, self.region)) == other.__hash__()

        if isinstance(other, (str, bytes)):
            return self.purpose == other

        if isinstance(other, tuple):
            return (self.purpose, self.currency, self.region) == other


class Instance(MongoModel, AppMixin):
    """

    """

    _id = fields.ObjectIdField(required=True, blank=False, primary_key=True)
    name = fields.CharField(required=True, blank=False)
    description = fields.CharField(required=False, blank=True)
    email = fields.CharField(required=False, blank=True)
    phone = fields.CharField(required=False, blank=True)
    type = fields.CharField(required=False, blank=True)
    domain = fields.CharField(required=False, blank=True)
    currency = ReferenceField(Currency, required=False, blank=True)
    user_id = fields.CharField(required=False, blank=False)
    free_delivery = fields.BooleanField(required=False, blank=True)
    default_currency = ReferenceField(Currency, required=False, blank=True)
    accounts = fields.EmbeddedDocumentListField(InstanceAccount, required=False, blank=True)
    supported_currencies = fields.EmbeddedDocumentListField(Currency, required=False, blank=True)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)

    def get_account(self, purpose, currency, region):
        """ Fetch profile from user """
        print(">>>>>>>>>>>>")
        print(purpose, currency, region)
        return next((p for p in self.accounts if p == (purpose, currency, region)), None)

    def add_account(self, **kwargs):
        """
        Tem
        """
        print("okkkk", kwargs)
        account = InstanceAccount(**kwargs)
        print(account)
        self.accounts.append(account)
        print(">>>>>>>>>>>>>")
        return self.save()

    class Meta:
        """
        Meta Class
        """
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True


class Status(MongoModel, AppMixin):
    code = fields.CharField(required=True, blank=False, primary_key=True)
    name = fields.CharField(required=True, blank=False)
    description = fields.CharField(required=False, blank=False)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)


class Customer(EmbeddedMongoModel):
    email = fields.CharField(required=False, blank=True)
    first_name = fields.CharField(required=False, blank=True)
    last_name = fields.CharField(required=False, blank=True)
    name = fields.CharField(required=False, blank=True)
    phone = fields.CharField(required=False, blank=True)
    street = fields.CharField(required=False, blank=True)
    street_line_2 = fields.CharField(required=False, blank=True)
    state = fields.CharField(required=False, blank=True)
    country = fields.CharField(required=False, blank=True)
    lat = fields.FloatField(required=False, blank=True)
    city = fields.CharField(required=False, blank=True)
    post_code = fields.CharField(required=False, blank=True)
    lng = fields.FloatField(required=False, blank=True)


class Item(EmbeddedMongoModel):
    sku = fields.CharField(required=False, blank=True)
    quantity = fields.IntegerField(required=False, blank=True)
    description = fields.CharField(required=False, blank=True)
    category = fields.CharField(required=False, blank=True)
    amount = fields.FloatField(required=False, blank=True)
    weight = fields.FloatField(required=False, blank=True)

    @property
    def total(self):
        """

        """
        return self.quantity * self.amount


class Invoice(MongoModel, AppMixin):
    """
    """

    code = fields.CharField(required=True, blank=False)
    reference_code = fields.CharField(required=False, blank=True)
    customer = fields.EmbeddedDocumentField(Customer, required=True, blank=False)
    items = fields.EmbeddedDocumentListField(Item, required=False, blank=True)
    merchant = fields.DictField(required=False, blank=True)
    payment_data = fields.DictField(required=False, blank=True)
    date_paid = fields.DateTimeField(required=False, blank=True)
    instance_id = fields.CharField(required=True, blank=False)
    region = fields.CharField(required=False, blank=True)
    status = fields.ReferenceField(Status, required=False, blank=True)
    payment_source_code = fields.CharField(blank=True)
    user_id = fields.CharField(required=False, blank=True)
    entity_id = fields.CharField(required=False, blank=True)
    discount = fields.FloatField(required=False, blank=True, default=0)
    currency = ReferenceField(Currency, required=False, blank=True)
    delivery_fee = fields.FloatField(required=False, blank=True)
    extra_data = fields.DictField(required=False, blank=True)
    sub_total = fields.FloatField(required=False, blank=True)
    total = fields.FloatField(required=False, blank=True)
    vat = fields.FloatField(required=False, blank=True)
    auto_approve = fields.BooleanField(required=False, blank=True)
    notify_customer = fields.BooleanField(required=False, blank=True)
    fx_rate = fields.FloatField(required=False, blank=True)
    fx_amount_receivable = fields.FloatField(required=False, blank=True)
    local_currency = fields.CharField(required=False, blank=True)
    amount_receivable = fields.FloatField(required=False, blank=True)
    transaction_charge = fields.FloatField(required=False, blank=True)
    vat_inclusive = fields.BooleanField(required=False, blank=True)
    amount_paid = fields.FloatField(required=False, blank=True)
    transaction_charge_rate = fields.FloatField(required=False, blank=True)
    transaction_charge_cap = fields.FloatField(required=False, blank=True)
    delivery_id = fields.CharField(required=False, blank=True)
    order_request_id = fields.CharField(required=False, blank=True)
    transaction_code = fields.CharField(required=False, blank=True)
    transaction_id = fields.CharField(required=False, blank=True)
    payment_id = fields.CharField(required=False, blank=True)
    instruction_history_id = fields.CharField(required=False, blank=True)
    transaction_reference = fields.CharField(required=False, blank=True)
    instruction_code = fields.CharField(required=False, blank=True)
    instruction_id = fields.CharField(required=False, blank=True)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True

    def calculate_fees(self):
        """

        """
        sub_total = roundUp(sum([item.amount * item.quantity for item in self.items])) if self.items else 0
        self.sub_total = sub_total
        total_ = self.sub_total
        if self.delivery_fee:
            total_ += self.delivery_fee
        if self.discount:
            total_ -= self.discount
        vat_rate = InvoicingConfiguration.objects.get({"instance_id": self.instance_id, "region": self.region}).vat_rate
        print(total_, vat_rate, "aa")
        vat = roundUp(sub_total - (sub_total / (vat_rate + 1))) if sub_total else 0

        if not self.vat_inclusive:
            total_ += vat

        self.vat = vat
        self.total = roundUp(total_)
        return self.save()

    @property
    def url(self):
        """

        """
        base_url = InvoicingConfiguration.objects.get({"instance_id": self.instance_id,
                                                       "region": self.region}).web_base_url

        return f"{base_url}/{str(self.code)}"

    @property
    def user(self):
        """

        """
        return Profile.objects.get({"user_id": self.user_id})

    @property
    def entity(self):
        """

        """
        return Entity.objects.get({"user_id": self.user_id})

    def payment_data_(self):
        """

        @return:
        """
        return dict(amount=self.total, currency=self.currency.code, instance_id=self.instance_id, intent="charge",
                    other_data={}, reference_code=self.code, instructions=[])


class SupportedCurrency(MongoModel, AppMixin):
    instance_id = fields.CharField()
    region = fields.CharField()
    code = fields.CharField(required=True)
    name = fields.CharField(required=False, blank=True)
    fx_charge = fields.FloatField(required=False, blank=True)
    enabled = fields.BooleanField(default=False)
    symbol = fields.CharField(required=False, blank=True)

    @property
    def rates(self):
        """

        """
        return [{"code": currency.code, "name": currency.name,
                 "value": calculate_exchange_rate(amount=1, currency=self.code, new_currency=currency.code,
                                                  markup_charge=self.fx_charge).get("markup_amount")}
                for currency in SupportedCurrency.objects.raw({"enabled": True, "code": {"$ne": self.code},
                                                               "region": self.region,
                                                               "instance_id": self.instance_id})]


class Reconciliation(MongoModel, AppMixin):
    """

    """
    status = fields.ReferenceField(Status, required=False, blank=True)
    payment_data = fields.DictField(required=False, blank=True)
    region = fields.CharField(required=False, blank=True)
    instance_id = fields.CharField(required=False, blank=True)
    amount = fields.FloatField(required=False, blank=True)
    checkout_id = fields.CharField(required=False, blank=True)
    entity_id = fields.CharField(required=False, blank=True)
    reference_code = fields.CharField(required=False, blank=True)
    code = fields.CharField(required=False, blank=True)
    fx_markup_amount = fields.FloatField(required=False, blank=True)
    fx_amount_received = fields.FloatField(required=False, blank=True)
    amount_available = fields.FloatField(required=False, blank=True)
    fx_markup_rate = fields.FloatField(required=False, blank=True)
    amount_received = fields.FloatField(required=False, blank=True)
    currency_received = fields.CharField(required=False, blank=True)
    fx_rate = fields.FloatField(required=False, blank=True)
    transaction_charge = fields.FloatField(required=False, blank=True)
    amount_payable = fields.FloatField(required=False, blank=True)
    currency = fields.ReferenceField(Currency, required=False, blank=True)
    username = fields.CharField(required=False, blank=True)
    name = fields.CharField(required=False, blank=True)
    email = fields.CharField(required=False, blank=True)
    transaction_charge_rate = fields.FloatField(required=False, blank=True)
    transaction_charge_cap = fields.FloatField(required=False, blank=True)
    phone = fields.CharField(required=False, blank=True)
    user_id = fields.CharField(required=False, blank=True)
    reference_id = fields.CharField(required=False, blank=True)
    instruction_code = fields.CharField(required=False, blank=True)
    instruction_history_id = fields.CharField(required=False, blank=True)
    completed_by = fields.DictField(required=False, blank=True)
    date_paid = fields.DateTimeField(required=False, blank=True)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)

    def charge_payment_data(self, profile_service):
        """

        :return:
        """

        profile = Entity.objects.get({"user_id": self.user_id})

        account = profile_service.get_individual_account(instance_id=self.instance_id, user_id=self.user_id,
                                                         entity_id=self.entity_id,
                                                         purpose="earnings", currency=self.currency.code)

        instance = Instance.objects.get({"_id": ObjectId(self.instance_id)})

        base = dict(account_key=None, amount=self.amount, currency=self.currency.code,
                    email=profile.email, phone=profile.phone, name=profile.name,
                    instance_id=self.instance_id, intent="charge", other_data=dict(region=self.region,
                                                                                   product_type="invoicing",
                                                                                   product_id=str(self.pk)),
                    reference_code=self.reference_code, source="account")
        instructions = [dict(action="invoice.reconciliation", amount=self.amount, currency=self.currency.code,
                             narration=f"Settlement of invoice payment [{self.reference_code}]", number=1,
                             reference_code=self.reference_code, type="debit",
                             account_key=instance.get_account(purpose="service",
                                                              region=self.region,
                                                              currency=self.currency.code).key,
                             user_id=self.user_id),
                        dict(action="invoice.reconciliation", amount=self.amount, currency=self.currency.code,
                             instance_id=self.instance_id,
                             narration=f"Settlement of invoice payment [{self.reference_code}]", number=2,
                             account_key=account.key,
                             reference_code=self.reference_code, type="credit")]

        base.update(instructions=instructions)

        return munchify(base)

    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True


class EmbeddedAddress(EmbeddedMongoModel):
    country = fields.CharField(required=False, blank=True)
    state = fields.CharField(required=False, blank=True)
    city = fields.CharField(required=False, blank=True)
    street = fields.CharField(required=False, blank=True)
    street_line_2 = fields.CharField(required=False, blank=True)
    lat = fields.CharField(required=False, blank=True)
    lng = fields.CharField(required=False, blank=True)
    post_code = fields.CharField(required=False, blank=True)


class Entity(MongoModel, AppMixin):
    """
    This model holds information about businesses on Sendbox that want to share access to staff members.
    Every entity must have at least one member, i.e the creator or a super admin
    """
    name = fields.CharField(required=False, blank=True)
    email = fields.CharField(required=False, blank=True)
    phone = fields.CharField(required=False, blank=True)
    currency = fields.ReferenceField(Currency, required=False, blank=True)
    type = fields.CharField(required=False, blank=True)
    user_id = fields.CharField(required=True, blank=False)
    region = fields.CharField(required=True, blank=False)
    address = fields.EmbeddedDocumentField(EmbeddedAddress, required=False, default={})
    instance_id = fields.CharField(required=True, blank=False)
    logo = fields.CharField(required=False, blank=True)
    enabled = fields.BooleanField(required=False, blank=True, default=False)
    accounts = fields.EmbeddedDocumentListField(Account, required=False, blank=True)
    description = fields.CharField(required=False, blank=True)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)

    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True

        indexes = [
            IndexModel([('domain', pymongo.ASCENDING), ('email', pymongo.ASCENDING),
                        ('instance_id', pymongo.ASCENDING), ('phone', pymongo.ASCENDING),
                        ("date_created", pymongo.DESCENDING)]),
            IndexModel([('domain', pymongo.ASCENDING), ('instance_id', pymongo.ASCENDING)],
                       partialFilterExpression={"domain": {"$type": "string"}},
                       unique=True)
        ]

    def get_account(self, purpose, currency):
        """ Fetch profile from user """
        print("the purpepepe", self.user_id, purpose, currency)
        print((p for p in self.accounts if p == (purpose, currency)), None)
        return next((p for p in self.accounts if p == (purpose, currency)), None)

    def add_account(self, **kwargs):
        """
        Tem
        """
        account = Account(**kwargs)
        self.accounts.append(account)
        return self.save()

