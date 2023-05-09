import settings
from App.custom.helpers import rest_post
from munch import munchify
from pprint import pprint


def get_accounts(**kwargs):
    print("calling payment profile")
    try:
        purpose = kwargs.get("purpose")
        res = rest_post(url="{}/engine/get_accounts".format(settings.HEADLESS_PAYMENTS_INTERNAL_BASE_URL),
                        data=dict(request_data=dict(**kwargs)))
        if not purpose:
            return munchify(res.get("response_data", {}))
        accounts = res.get("response_data", {}).get("accounts", [])
        print(purpose, "thisispppiiii")
        print("aaaaaaaa", accounts)
        return {"status": "success",
                "account": next(iter(account for account in accounts if account.get("purpose") == purpose), None)}
    except Exception as e:
        log_error(e, get_accounts, **kwargs)
        raise Exception


def initiate_checkout(**kwargs):
    print("calling initiate checkout")
    try:

        res = rest_post(url="{}/engine/checkout".format(settings.HEADLESS_PAYMENTS_INTERNAL_BASE_URL),
                        data=dict(request_data=dict(**kwargs)))
        return munchify(res.get("response_data", {}))
    except Exception as e:
        log_error(e, initiate_checkout, **kwargs)
        raise Exception


def get_txref(**kwargs):
    """

    @param kwargs:
    @return:
    """
    try:

        res = rest_post(url="{}/engine/get_txref".format(settings.HEADLESS_PAYMENTS_INTERNAL_BASE_URL),
                        data=dict(request_data=dict(reference_code=kwargs.get("reference_code"))))

        return munchify(res.get("response_data", {}))
    except Exception as e:
        log_error(e, get_txref, **kwargs)
    raise Exception


def verify_transaction(**kwargs):
    """

    @param kwargs:
    @return:
    """
    try:

        res = rest_post(url="{}/engine/verify_transaction".format(settings.HEADLESS_PAYMENTS_INTERNAL_BASE_URL),
                        data=dict(request_data=dict(reference_code=kwargs.get("reference_code"),
                                                    user_id=kwargs.get("user_id"))))

        return munchify(res.get("response_data", {}))
    except Exception as e:
        log_error(e, get_txref, **kwargs)
    raise Exception


def charge_account(**kwargs):
    print("calling charge account")
    try:

        res = rest_post(url="{}/engine/charge_account".format(settings.HEADLESS_PAYMENTS_INTERNAL_BASE_URL),
                        data=dict(request_data=dict(**kwargs)))
        return munchify(res.get("response_data", {}))
    except Exception as e:
        log_error(e, initiate_checkout, **kwargs)
        raise Exception


def log_error(e, self, **data):
    """describe a grpc error in a log"""

    print("*" * 200)
    error_data = dict({"request_method": self.__name__, "request_data": data, "location": "'%s': line %s " % (
        self.__code__.co_filename, self.__code__.co_firstlineno)})
    try:
        error_data.update({"error_class": "GRPC SERVER", "error_details": e.details})
    except Exception as ex:
        try:
            error_data.update({"error_class": "LOCAL SERVER", "error_details": e.message})
        except Exception as ed:
            error_data.update({"error_class": "LOCAL SERVER", "error_details": str(e)})

    pprint(error_data)
    print("*" * 200)
