# coding=utf-8
"""
users.py
@Author: Jason Nwakaeze
@Date: August 25, 2021
"""

from sendbox_core.services.odm import ServiceFactory
from App.async_ import *
from App.grpc_.clients.payments_rpc import get_accounts

BaseProfileService = ServiceFactory.create_service(Profile)
BaseInstanceService = ServiceFactory.create_service(Instance)
BaseEntityService = ServiceFactory.create_service(Entity)


class InstanceService(BaseInstanceService):
    """
    Service Class responsible for manipulating merchant settings


    Methods
    -------

    register(instance_id, **kwargs)
    registers the merchant settings of a particular merchant and saves it in the db.

    """

    @classmethod
    def register(cls, **kwargs):
        """
        @param kwargs:
        @type kwargs:
        @return:
        @rtype:
        """
        pprint(kwargs)
        return cls.create(**kwargs, ignored_args=["date_created", "last_updated"])

    @classmethod
    def get_individual_account(cls, obj_id, region, currency, purpose="service", **kwargs):
        """

        @param obj_id:
        @param purpose:
        @param region:
        @param currency:
        @param kwargs:
        @return:
        """
        instance = cls.get(obj_id)
        account = instance.get_account(purpose=purpose, region=region, currency=currency)
        if account: return account
        fetch_data = dict(instance_id=obj_id, user_id=instance.user_id, purpose=purpose, currency=currency,
                          region=region)

        account_res = get_accounts(**fetch_data)
        if account_res.get("status") not in ["success", "successful"]:
            raise

        print(">>>>>>>>>help me", account_res)
        account_ = account_res.get('account')
        print("oooooppppsss>>>>>>>>>>>>", account_)
        account_data = munchify(dict(key=account_.get("key"), type=account_.get("type"),
                                     purpose=account_.get("purpose"), is_main=account_.get("is_main"),
                                     name=account_.get("name"), email=account_.get("email"),
                                     phone=account_.get("phone"), currency=account_.get("currency"),
                                     region=account_.get("region"),
                                     is_anonymous=account_.get("is_anonymous")))
        print(account_data)
        instance.add_account(**account_data)
        return account_data

    @classmethod
    def update_settings(cls, **kwargs):
        """

        @param kwargs:
        @return:
        """


class EntityService(BaseEntityService):
    """
    Service Class responsible for manipulating merchant settings


    Methods
    -------

    register(instance_id, **kwargs)
    registers the merchant settings of a particular merchant and saves it in the db.

    """

    @classmethod
    def register(cls, **kwargs):
        """
        @param kwargs:
        @type kwargs:
        @return:
        @rtype:
        """
        pprint(kwargs)
        kwargs["_id"] = kwargs.get("entity_id")
        return cls.create(**kwargs, ignored_args=["date_created", "last_updated"])

    @classmethod
    def build_merchant_data(cls, user_id, **kwargs):
        """

        """
        print(user_id)
        entity = cls.objects.get({"user_id": user_id})
        address = entity.address
        data = dict(name=entity.name, phone=entity.phone, email=entity.email, username=entity.name,
                    user_id=entity.user_id, instance_id=entity.instance_id, region=entity.region,
                    entity_id=str(entity.pk), id=str(entity.pk))
        if address:
            data.update(country=address.country, state=address.state, city=address.city, street=address.street,
                        street_line_2=address.street_line_2, lat=address.lat, lng=address.lng,
                        post_code=address.post_code, )
        return data

    @classmethod
    def get_by_user_id(cls, user_id):
        """
        get the profile object by the user_id of the profile as seen on auth
        :param user_id: auth user_id
        :return:
        """

        try:
            pro = cls.objects.raw({"user_id": user_id, "entity_id": None}).first()

            print(pro)
        except Exception as e:
            print(e, "-------eoejeee")
            pro = None
        return pro

    @classmethod
    def get_individual_account(cls, instance_id, entity_id, user_id=None, purpose="earning", currency="NGN",
                               **kwargs):
        """

        @param user_id:
        @param entity_id:
        @param currency:
        @param instance_id:
        @param purpose:
        @param region:
        @param auto_create:
        @param kwargs:
        @return:
        """
        find_data = dict(instance_id=instance_id, _id=ObjectId(entity_id))

        print(find_data, "curreoen", currency, user_id)
        profile = cls.find_one(find_data)
        print(purpose, currency, ".>>>>>>>>>>>>")
        pprint(profile)
        account = profile.get_account(purpose=purpose, currency=currency)

        print("gottemm+++", account)
        if account: return account
        fetch_data = dict(instance_id=profile.instance_id, purpose=purpose, entity_id=entity_id,
                          currency=currency)
        pprint(fetch_data)
        account_res = get_accounts(**fetch_data)
        if account_res.get("status") not in ["success", "successful"]:
            raise
        account_ = account_res.get('account')
        print('>>>>>>>>>>>>,,,,,,,,', account_)
        if not account_:
            return {}

        account_data = munchify(dict(key=account_.get("key"), type=account_.get("type"),
                                     purpose=account_.get("purpose"), is_main=account_.get("is_main"),
                                     name=account_.get("name"), email=account_.get("email"),
                                     phone=account_.get("phone"), currency=account_.get("currency"),
                                     region=account_.get("region"),
                                     is_anonymous=account_.get("is_anonymous")))

        if purpose != "credits":
            profile.add_account(**account_data)
        account_data.update(balance=account_.get("balance"))
        return account_data


class ProfileService(BaseProfileService):
    """
    ProfileService
    """

    @classmethod
    def register(cls, **kwargs):
        """
        @param kwargs:
        @type kwargs:
        @return:
        @rtype:
        """
        print("in prof===>")
        pprint(kwargs)
        return cls.create(**kwargs)

    @classmethod
    def get_by_entity_id(cls, entity_id):
        """

        """
        return cls.objects.get({"entity_id": entity_id})

    @classmethod
    def get_individual_account(cls, instance_id, entity_id=None, user_id=None, purpose="purchases", currency="NGN",
                               **kwargs):
        """

        @param user_id:
        @param entity_id:
        @param currency:
        @param instance_id:
        @param purpose:
        @param region:
        @param auto_create:
        @param kwargs:
        @return:
        """
        find_data = dict(instance_id=instance_id, user_id=user_id)

        print(find_data, "curreoen", currency, user_id)
        profile = cls.find_one(find_data)
        print(purpose, currency, ".>>>>>>>>>>>>")
        pprint(profile)
        account = profile.get_account(purpose=purpose, currency=currency)

        print("gottemm+++", account)
        if account: return account
        fetch_data = dict(instance_id=profile.instance_id, user_id=profile.user_id, purpose=purpose,
                          currency=currency)
        if profile.entity_id:
            fetch_data.update(entity_id=entity_id)

        pprint(fetch_data)
        account_res = get_accounts(**fetch_data)
        if account_res.get("status") not in ["success", "successful"]:
            raise
        account_ = account_res.get('account')
        print('>>>>>>>>>>>>,,,,,,,,', account_)
        if not account_:
            return {}

        account_data = munchify(dict(key=account_.get("key"), type=account_.get("type"),
                                     purpose=account_.get("purpose"), is_main=account_.get("is_main"),
                                     name=account_.get("name"), email=account_.get("email"),
                                     phone=account_.get("phone"), currency=account_.get("currency"),
                                     region=account_.get("region"),
                                     is_anonymous=account_.get("is_anonymous")))

        if not profile.is_anonymous and purpose != "credits":
            profile.add_account(**account_data)
        account_data.update(balance=account_.get("balance"))
        return account_data

    @classmethod
    def build_merchant_data(cls, user_id, **kwargs):
        """

        """
        print(user_id)
        profile = cls.objects.get({"user_id": user_id})
        return dict(name=profile.name, phone=profile.phone, email=profile.email, username=profile.username,
                    user_id=profile.user_id, instance_id=profile.instance_id, region=profile.region,
                    id=str(profile.pk))

    @classmethod
    def get_by_user_id(cls, user_id):
        """
        get the profile object by the user_id of the profile as seen on auth
        :param user_id: auth user_id
        :return:
        """

        try:
            pro = cls.objects.raw({"user_id": user_id, "entity_id": None}).first()

            print(pro)
        except Exception as e:
            print(e, "-------eoejeee")
            pro = None
        return pro
