from sendbox_core.base.utils import code_generator, generate_random_code, number_format
from sendbox_core.services.odm import ServiceFactory

from App.custom.helpers import format_address, to_dict
from App.grpc_.clients.payments_rpc import *
from App.models import *
from App.services.core import InvoicingConfigurationService
from App.services.profile import ProfileService, InstanceService, EntityService
from App.async_ import notify_parties, do_reconciliation

BaseInvoiceService = ServiceFactory.create_service(Invoice)
BaseReconciliationService = ServiceFactory.create_service(Reconciliation)


class InvoiceService(BaseInvoiceService):

    @classmethod
    def register(cls, instance_id, user_id, **kwargs):
        """
        """
        profile = EntityService.build_merchant_data(user_id)

        auto_approve = kwargs.get("auto_approve")
        status = "pending" if auto_approve else "drafted"
        invoice = cls.create(code=generate_random_code(prefix="INV"), instance_id=instance_id, user_id=user_id,
                             status=status,
                             entity_id=profile.get("id"),
                             merchant=profile, region=profile.get("region"), **kwargs)

        invoice = invoice.calculate_fees()
        other_data = cls.validate_invoice(amount=invoice.total,
                                          currency=invoice.currency.code, instance_id=instance_id, user_id=user_id)
        invoice = cls.update(invoice.pk, **other_data)

        customer = invoice.customer
        user = invoice.entity
        payment_data = invoice.payment_data_()
        anon_user_id = Profile.objects.raw({"is_anonymous": True}).first().user_id
        payment_account = ProfileService.get_individual_account(user_id=anon_user_id,
                                                                instance_id=instance_id,
                                                                purpose="purchases", currency=invoice.currency.code,
                                                                region=invoice.region)

        instructions = [dict(account_key=payment_account.key, action="order.pay", amount=invoice.total,
                             reference=invoice.code, name=customer.name, email=customer.email, phone=customer.phone,
                             type="debit", narration="Payment of Invoice", number=1),
                        dict(account_key=InstanceService.get_individual_account(obj_id=invoice.instance_id,
                                                                                region=invoice.region,
                                                                                currency=invoice.currency.code).key,
                             action="order.pay",
                             amount=invoice.total, reference=invoice.code,
                             type="credit", narration="Payment of Invoice", number=2)]
        payment_data.update(instructions=instructions)

        checkout_da = initiate_checkout(**dict(reference_code=invoice.code,
                                               currency=invoice.currency.code,
                                               name=customer.name,
                                               callback_urls=[f"{settings.HEADLESS_INVOICING_INTERNAL_BASE_URL}"
                                                              f"/engine/validate_invoice_payment"],
                                               user_id=anon_user_id,
                                               amount=invoice.total,
                                               region=invoice.region,
                                               instance_id=invoice.instance_id,
                                               merchant=dict(name=user.name, phone=user.phone,
                                                             email=user.email, pk=str(user.user_id)),
                                               email=customer.email, phone=customer.phone,
                                               product_type="invoicing",
                                               payment_data=payment_data,
                                               items=[dict(quantity=item.quantity, unit_price=item.amount,
                                                           sku=item.sku,
                                                           total_price=item.total, reference=invoice.code,
                                                           name=item.description, instance_id=invoice.instance_id)
                                                      for item in invoice.items]))

        invoice = cls.update(invoice.pk, payment_data=dict(checkout_id=checkout_da.get("url_hash"),
                                                           status=checkout_da.get("status"),
                                                           entity_id=checkout_da.get("entity_id"),
                                                           currency=checkout_da.get("currency"),
                                                           reference_code=invoice.code,
                                                           payment_source_code=invoice.payment_source_code,
                                                           amount=checkout_da.get('payment_data', {}).get("amount")))

        if auto_approve:
            try:
                payload = cls.prepare_notification_data(invoice.pk)
                notify_parties("invoice.request", payload, invoice.pk, instance_id)
            except Exception as e:
                print("sending notification error...", e)

        return invoice

    @classmethod
    def validate_invoice(cls, currency, instance_id, amount, user_id, **kwargs):
        """

        """

        profile_currency = kwargs.get("local_currency")
        config = InvoicingConfigurationService.get_config(instance_id=instance_id, currency=currency,
                                                          keys=["LOCAL_TRANSACTION_CHARGE",
                                                                "TRANSACTION_CHARGE_CAP",
                                                                "INTERNATIONAL_TRANSACTION_CHARGE"])

        entity = EntityService.get_by_user_id(user_id)
        if not profile_currency:
            profile_currency = entity.currency.code

        resp = dict(currency=currency, amount=amount, instance_id=instance_id, local_currency=profile_currency)
        if profile_currency == currency:
            tr_charge_rate = config.get("LOCAL_TRANSACTION_CHARGE", 0)
            tr_charge = amount * tr_charge_rate
            tr_charge_cap = config.get("TRANSACTION_CHARGE_CAP", 0)
            if tr_charge_cap and tr_charge > tr_charge_cap:
                tr_charge = tr_charge_cap
            amount_receivable = amount - tr_charge
            resp.update(amount_receivable=amount_receivable, transaction_charge=tr_charge, fx_rate=1,
                        transaction_charge_rate=tr_charge_rate,
                        transaction_charge_cap=tr_charge_cap,
                        fx_amount_receivable=amount_receivable, actual_fx_amount=amount_receivable)
        else:
            tr_charge_rate = config.get("INTERNATIONAL_TRANSACTION_CHARGE", 0)
            tr_charge = amount * tr_charge_rate
            tr_charge_cap = config.get("TRANSACTION_CHARGE_CAP", 0)
            print("I am charge", tr_charge_cap, tr_charge, tr_charge>tr_charge_cap)
            if tr_charge_cap and tr_charge > tr_charge_cap:
                tr_charge = tr_charge_cap
            print("findall", tr_charge)
            amount_receivable = amount - tr_charge
            curr = SupportedCurrency.objects.get({"code": profile_currency, "instance_id": instance_id})
            conv = calculate_exchange_rate(amount=amount_receivable, currency=currency,
                                           new_currency=profile_currency,
                                           markup_charge=curr.fx_charge)
            fx_amount_receivable = conv.get("markup_amount")
            resp.update(fx_rate=conv.get("markup_rate"),
                        actual_fx_rate=conv.get("currency_rate"),
                        actual_fx_amount=conv.get("amount"),
                        fx_amount_receivable=fx_amount_receivable,
                        transaction_charge_rate=tr_charge_rate,
                        transaction_charge_cap=tr_charge_cap,
                        amount_receivable=amount_receivable, transaction_charge=tr_charge)

        return resp

    @classmethod
    def prepare_notification_data(cls, obj_id):
        """

        :param obj_id:
        :type obj_id:
        :return:
        :rtype:
        """
        invoice = cls.get(obj_id)
        invoice_items = invoice.items
        addrss_customer = to_dict(invoice.customer)
        addrss_merchant = invoice.merchant
        destination_address = format_address(addrss_customer)
        origin_address = format_address(addrss_merchant)
        items = [{"weight": str(item.weight),
                  "quantity": item.quantity,
                  "description": item.description,
                  "value": number_format(item.amount),
                  "sku": item.sku if item.sku else ""}
                 for item in invoice_items]

        payment_url = invoice.url

        payload = dict(origin_name=invoice.merchant.get("name"),
                       items=items, transaction_charge=number_format(invoice.transaction_charge),
                       destination_phone=invoice.customer.phone,
                       destination_email=invoice.customer.email,
                       destination_name=invoice.customer.name,
                       destination_address=destination_address,
                       origin_address=origin_address,
                       code=invoice.code, origin_email=invoice.merchant.get("email"),
                       origin_phone=invoice.merchant.get("phone"),
                       fee=number_format(invoice.total),

                       delivery_fee=number_format(invoice.delivery_fee),
                       subtotal=number_format(invoice.sub_total),
                       discount=number_format(invoice.discount),
                       currency=invoice.currency.code, payment_url=payment_url)

        return payload

    @classmethod
    def validate_invoice_payment(cls, reference_code, **kwargs):
        invoice = cls.find_one({"code": reference_code})

        tr_data = verify_transaction(reference_code=reference_code, user_id=kwargs.get("user_id"),
                                     transaction_code=kwargs.get("txref"))
        print("inverify===>")
        pprint(tr_data)
        if invoice.status.code not in ["drafted", "pending"]:
            return invoice
        print(invoice.code, "-------------+==2///")
        payment_data = invoice.payment_data
        if tr_data.get("status") in ["success", "successful"]:
            payment_data.update(status="successful", payment_source_code=tr_data.get("source"))
            return cls.activate_invoice(obj_id=str(invoice.pk), transaction_code=tr_data.get('code'),
                                        amount_paid=tr_data.get("amount"),
                                        payment_data=payment_data,
                                        payment_source_code=tr_data.get("source"),
                                        date_paid=tr_data.get("date_created"),
                                        instruction_code=tr_data.get("instruction_code"),
                                        instruction_history_id=tr_data.get("instruction_history_id"),
                                        instruction_id=tr_data.get("instruction_id"))

    @classmethod
    def activate_invoice(cls, obj_id, **kwargs):
        """

        """

        invoice = cls.update(obj_id, status="paid", **kwargs)
        do_reconciliation(invoice_id=str(obj_id))

        # :TODO notify customer and merchant of successful payment
        try:
            payload = cls.prepare_notification_data(invoice.pk)
            notify_parties("invoice.paid", payload, invoice.pk, invoice.instance_id)
        except Exception as e:
            print("sending notification error...", e)
        return invoice


class ReconciliationService(BaseReconciliationService):

    @classmethod
    def register(cls, **kwargs):
        """

        """
        print("begin recon")

        invoice = InvoiceService.get(kwargs.get("invoice_id"))
        recon = cls.find_one({"reference_code": invoice.code, "reference_id": str(invoice.pk)})
        if recon:
            return recon
        data = dict(status="pending", region=invoice.region, instance_id=invoice.instance_id,
                    code=generate_random_code(),
                    reference_id=str(invoice.pk),
                    amount_received=invoice.amount_paid, currency_received=invoice.currency.code,
                    reference_code=invoice.code, username=invoice.user.username,
                    email=invoice.user.email, phone=invoice.user.phone, user_id=invoice.user_id,
                    entity_id=invoice.entity_id)

        entity = EntityService.get(invoice.entity_id)
        profile_currency = entity.currency.code
        invoice_currency = invoice.currency.code

        charges_data = InvoiceService.validate_invoice(currency=invoice_currency, instance_id=invoice.instance_id,
                                                       amount=invoice.amount_paid, user_id=invoice.user_id)
        amount_payable = charges_data.get("amount_receivable", 0)
        fx_amount_payable = charges_data.get("fx_amount_receivable", 0)
        data.update(amount_payable=amount_payable,
                    fx_amount_payable=fx_amount_payable,
                    amount=charges_data.get("actual_fx_amount"),
                    amount_available=charges_data.get("amount") - amount_payable,
                    currency=profile_currency,
                    fx_markup_rate=charges_data.get("fx_rate"), fx_rate=charges_data.get("actual_fx_rate"),
                    transaction_charge=charges_data.get('transaction_charge'))
        recon = cls.create(**data)
        charge_payment_data = recon.charge_payment_data(profile_service=EntityService)
        charge_payment_data.update(allow_negative=True, negative_reason="over_draft")
        trans = charge_account(**charge_payment_data)

        if trans.status in ["successful"]:
            try:
                payload = InvoiceService.prepare_notification_data(invoice.pk)
                notify_parties("invoice.paid", payload, invoice.pk, invoice.instance_id)
            except Exception as e:
                print("sending notification error...", e)

            recon = cls.update(recon.pk, transaction_code=trans.txref,
                               date_paid=datetime.now(), status="successful",
                               instruction_code=trans.instruction_code,
                               instruction_history_id=trans.instruction_history_id)

        return recon
