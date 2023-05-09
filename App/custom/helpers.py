# from sendbox_core.integrations.falcon_integration.utils import *
from pprint import pprint

"""
helpers.py

shared functions and methods that are required in multiple places
"""
import hashlib
import hmac

import phonenumbers
import pycountry
from falcon.media import JSONHandler
from sendbox_core.base.utils import CustomJSONEncoder, roundUp
from validator_collection import checkers
import re
# from falcon.util import json
import json
import six
import requests
from pprint import pprint
from falcon.media import BaseHandler
from datetime import datetime, timedelta
import calendar
import settings

country_code = {"NG": "Nigeria",
                "GH": "Ghana",
                "KE": "Kenya",
                "SA": "South Africa"}


def get_obj_code(obj, attr='code'):
    """get the code of a reference field object"""
    try:
        atr = getattr(obj, attr)
        if atr:
            return atr.lower()
        return obj.lower()
    except Exception as e:
        # print e
        return obj


def dprint(message, obj):
    """ """
    print(message)
    pprint(obj)


def prepare_user_data(data):
    """ Helper function to clean up user data before saving it """

    name = data.get("name", "").strip()
    username = data.get("username", "").strip().lower()
    email = data.get("email", None)
    country_code = data.pop("country_code", "NG")
    phone = data.get("phone")

    try:
        parsed_phone = phonenumbers.parse(phone, country_code)
        phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.phonenumberutil.NumberParseException:
        # fail silently because at this point the info is already validated
        raise

    country = pycountry.countries.get(alpha_2=country_code).alpha_2
    email = None if not email else email.strip().lower()
    data.update({
        "name": name,
        "username": username,
        "phone": phone.strip().lower(),
        "email": email,
        "country": country
    })

    city = data.get("city", None)
    state = data.get("state", None)
    street = data.get("street", None)

    if city and state and street:
        address = dict(name=name, email=email, phone=phone, street=street, city=city, state=state,
                       country=country)
        data.update(address=address)
    return data


def phone_number_validator(phone, country_code="NG"):
    """ Custom phone number validator to check that all phone numbers are unique and available """

    try:
        parsed_phone = phonenumbers.parse(phone, country_code)
        if not phonenumbers.is_valid_number(parsed_phone) and not str(parsed_phone.national_number).startswith("901"):
            return None
        phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.phonenumberutil.NumberParseException:
        return None
    return phone


def email_address_validation(email):
    email_pattern = re.compile(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$")

    if checkers.is_email(email) or email_pattern.match(email):
        return email
    return None


def generate_hmac_hash(hash_key, data, **kwargs):
    """

    :param hash_key:
    :param data:
    :param kwargs:
    :return:
    """

    hash_ = hmac.new(hash_key.encode("utf-8"), data.encode("utf-8"), hashlib.sha512).hexdigest()
    return hash_


def check_hmac_hash(hash_key, hash_, data, **kwargs):
    """

    :param hash_key:
    :param hash_:
    :param data:
    :param kwargs:
    :return:
    """
    to_hash = generate_hmac_hash(hash_key=hash_key, data=data)
    if to_hash != hash_:
        return False
    return True


class JsonHandler(JSONHandler):

    def serialize(self, media, content_type):
        if not content_type:
            content_type = 'application/json'
        result = json.dumps(media, ensure_ascii=False, cls=CustomJSONEncoder)
        pprint(result)
        if six.PY3 or not isinstance(result, bytes):
            return result.encode('utf-8')

        return result

    def _serialize_s(self, media, content_type=None) -> bytes:
        return json.dumps(media, ensure_ascii=False, cls=CustomJSONEncoder).encode()


def rest_post(url, data={}, method_name="post", **kwargs):
    """

    :param url:
    :param method_name:
    :param data:
    :param kwargs:
    :return:
    """
    res = dict(req_status='failed')
    try:
        headers = {"Content-Type": "application/json", "Accept": "application/json",
                   "Method": "POST", "Cache-Control": "no-cache", "User-Agent": "python/sendbox-api"}

        headers.update(**kwargs.get("headers", {}))
        params = kwargs.get("params", {})
        if method_name == "get":
            resp = requests.get(url, headers=headers, params=params)
        elif method_name == "put":
            resp = requests.put(url, json=data, headers=headers)
        else:
            resp = requests.post(url, data=json.dumps(data), headers=headers)

        print(resp.status_code)
        resp_data = resp.json()
        resp_data.update(req_status='success', message="Success", req_status_code=resp.status_code)
        pprint(resp_data)
        return resp_data
    except Exception as e:
        print(e)
        res.update(message=str(e))

    return res


def get_start_end(days=None, month=None, year=None, month_interval=1, **kwargs):
    """

    :param days:
    :param month:
    :param year:
    :param month_interval:
    :param kwargs:
    :return:
    """
    type_ = kwargs.get("type_")
    day = kwargs.get("day")

    today = datetime.today()

    if not month:
        month = today.month
    if not year:
        year = today.year

    if month > 12:
        year += 1
        month -= 12
    start_date = today.replace(month=month, year=year, day=1, hour=0, minute=0)

    if month_interval > 1:
        month = (month + month_interval) - 1

    if not days:
        days = calendar.monthrange(year=year, month=month)[1] - 1
    to_replace = dict(month=month, hour=23, minute=59)

    if type_ and type_.lower() == 'daily':
        days += 1
        dayt = 1 if day > days else day
        month = start_date.month + 1 if day > days else start_date.month
        year = start_date.year
        if month > 12:
            year += 1
            month -= 12

        start_date = start_date.replace(month=month, day=dayt, year=year)
        to_replace.update(day=start_date.day, month=start_date.month, year=start_date.year)

    if type_ and type_.lower() == 'weekly':
        days += 1
        dayt = 1 if day and day > days else day
        print(dayt, month)
        start_date = start_date.replace(month=month, day=dayt)
        start_date -= timedelta(days=start_date.weekday())

        month = start_date.month + 1 if day > days else start_date.month
        end = start_date + timedelta(days=6)
        to_replace.update(month=end.month, year=end.year, day=end.day)
    end_date = (start_date + timedelta(days=days))
    end_date = end_date.replace(**to_replace)
    custom_start = kwargs.get("custom_start", {})
    start_date = start_date.replace(day=custom_start.get("day", start_date.day),
                                    month=custom_start.get("month", start_date.month),
                                    year=custom_start.get("year", start_date.year))
    custom_end = kwargs.get("custom_end", {})
    end_date = end_date.replace(day=custom_end.get("day", end_date.day), month=custom_end.get("month", end_date.month),
                                year=custom_end.get("year", end_date.year))

    return start_date.replace(second=0, microsecond=0), end_date.replace(second=0, microsecond=0)


class TextHandler(BaseHandler):

    def deserialize(self, media):
        print("i am mediaaaaaa======", media, media.decode())

        return dict(body=media.decode())

    def serialize(self, obj):
        print("i am serirr======", obj)
        return obj


def format_address(address):
    """

    :param address:
    :return:
    """
    street = address.get("street") if address.get("street") else ""
    city = address.get("city") if address.get("city") else ""
    country = country_code.get(address.get("country"), "") if address.get("country") else ""
    to_format = [street, city, address.get("state"), country]
    _address = ",".join(to_format).replace("  ", "")
    return _address


def calculate_buy(amount, currency, new_currency, markup_charge=0, rate_data=None):
    """"""
    currency_rate = rate_data.get(new_currency) if rate_data else None
    if not currency_rate:
        runt = rest_post(url=settings.FLUTTERWAVE_RATES_API, method_name="get",
                         params={"from": currency, "to": new_currency, "amount": 1},
                         headers={"Authorization": f"Bearer {settings.FLUTTERWAVE_RATES_SECRET_KEY}"})
        currency_rate = runt.get("data", {}).get("rate")
    currency_rate = roundUp(currency_rate, 2)
    currency_amount = roundUp(amount * float(currency_rate))
    data = dict(currency_rate=currency_rate, amount=currency_amount, markup_amount=currency_amount,
                markup_rate=currency_rate)
    print("i ammmmchhahrr", markup_charge)
    if markup_charge:
        markup_rate = currency_rate - markup_charge
        print("iiiiepppp", currency_rate, markup_rate, markup_charge)
        data.update(markup_rate=markup_rate, markup_amount=roundUp(amount * float(markup_rate)))
    return data


def calculate_sell(amount, currency, new_currency, markup_charge=0, rate_data=None):
    """

    """

    currency_rate = rate_data.get(new_currency) if rate_data else None
    if not currency_rate:
        runt = rest_post(url=settings.FLUTTERWAVE_RATES_API, method_name="get",
                         params={"from": currency, "to": new_currency, "amount": 1},
                         headers={"Authorization": f"Bearer {settings.FLUTTERWAVE_RATES_SECRET_KEY}"})
        currency_rate = runt.get("data", {}).get("rate")
    currency_amount = roundUp(amount * float(currency_rate))
    data = dict(currency_rate=currency_rate, amount=currency_amount, markup_amount=currency_amount,
                markup_rate=currency_rate)
    if markup_charge:
        markup_rate = currency_rate - markup_charge
        data.update(markup_rate=markup_rate, markup_amount=roundUp(amount * float(markup_rate)))
    return data


def calculate_exchange_rate(amount, currency, new_currency, markup_charge=None,
                            rate_type="buy"):
    """

    :param amount:
    :type amount:
    :param amount:
    :param currency:
    :type currency:
    :param new_currency:
    :type new_currency:
    :param markup_charge:
    :type markup_charge:
    :param rate_type:
    :type rate_type:
    :return:
    :rtype:
    """

    from App import redis

    excr_key = f"excr_{currency.lower()}"
    redis_excr = redis.get(excr_key) or "{}"
    print("excr_key", redis_excr)
    excr_rate = json.loads(redis_excr)

    rate_data = excr_rate.get(rate_type, {})

    rate_conv = calculate_buy(amount=amount, currency=currency,
                              new_currency=new_currency,
                              markup_charge=markup_charge, rate_data=rate_data) if rate_type == "buy" \
        else calculate_sell(amount=amount, currency=currency, new_currency=new_currency,
                            markup_charge=markup_charge, rate_data=rate_data)

    currency_rate = rate_conv.get("currency_rate")
    print(excr_key, new_currency, currency_rate)
    rate_data.update({new_currency: currency_rate})
    excr_rate.update({rate_type: rate_data})
    redis.setex(excr_key, timedelta(days=1), json.dumps(excr_rate))
    return rate_conv


def to_dict(obj, exclude=None, do_dump=False):
    """

    @param exclude:
    @param do_dump:
    @return:

    Parameters
    ----------
    obj
    obj
    """

    from pymodm import MongoModel, EmbeddedMongoModel

    if isinstance(obj, (MongoModel, EmbeddedMongoModel)):
        d = to_custom_son(obj, exclude=exclude).to_dict()
        # [d.pop(i, None) for i in exclude]
        return json.loads(json.dumps(d, default=str)) if do_dump else d
    return obj.__dict__


def to_custom_son(obj, exclude=None):
    """Get this Model back as a :class:`~bson.son.SON` object.

    :returns: SON representing this object as a MongoDB document.

    """
    from bson import SON
    from pymodm.context_managers import no_auto_dereference
    son = SON()
    exclude = exclude if exclude else []
    with no_auto_dereference(obj):
        for field in obj._mongometa.get_fields():
            if field.is_undefined(obj):
                continue
            if exclude and field.attname in exclude:
                continue
            value = obj._data.get_python_value(field.attname, field.to_python)
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
