from sendbox_core.base.exceptions import ObjectNotFoundException
from sendbox_core.base.utils import generate_key, generate_random_code, code_generator
from sendbox_core.services.odm import ServiceFactory
from App.models import *

from cryptography.fernet import Fernet

StatusService = ServiceFactory.create_service(Status)
BaseSupportedCurrencyService = ServiceFactory.create_service(SupportedCurrency)
BaseInvoicingConfigurationService = ServiceFactory.create_service(InvoicingConfiguration)


class InvoicingConfigurationService(BaseInvoicingConfigurationService):

    @classmethod
    def get_config(cls, instance_id, currency="NGN", keys=None, region=None, **kwargs):
        """

        """

        print(instance_id, currency)
        pay_config = cls.find_one({"instance_id": instance_id, "currency": currency})
        print(pay_config)
        config = pay_config.internal_data.get(f"{settings.env}")
        keys = keys if keys else config.keys()

        new_config = dict(obj=pay_config)
        for key in keys:
            config_value = config.get(key)
            if not config_value:
                continue
            new_config[key] = cls.decrypt_config(config_value)
        return munchify(new_config)

    @classmethod
    def register(cls, instance_id, region, currency, config_data, **kwargs):
        """

        """
        pay_config = cls.find_one({"instance_id": instance_id, "currency": currency, "region": region})
        internal_data = pay_config.internal_data if pay_config.internal_data else {}
        config = internal_data[f"{settings.env}"]
        for key, value in config_data.items():
            config.update({key: cls.encrypt_config(value)})

        internal_data.update({f"{settings.env}": config})
        return cls.update(pay_config.pk, internal_data=internal_data)

    @classmethod
    def encrypt_config(cls, value):
        """

        """
        fernet = Fernet(settings.CONFIG_ENCRYPTION_KEY.encode())
        return fernet.encrypt(value.encode()).decode()

    @classmethod
    def decrypt_config(cls, value):
        """

        """
        fernet = Fernet(settings.CONFIG_ENCRYPTION_KEY.encode())
        res = value
        try:
            res = fernet.decrypt(value.encode()).decode()
        except Exception as e:
            print(e)
        return res


class SupportedCurrencyService(BaseSupportedCurrencyService):

    @classmethod
    def get_currencies(cls, instance_id, **kwargs):
        """

        """
        currencies = cls.objects.raw({"instance_id": instance_id})
        for currency in currencies:
            """"""


# pay.sendbox.co/invoice/{invoice_id}
