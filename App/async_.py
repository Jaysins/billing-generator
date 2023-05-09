import json

from App import celery_app as celery
import settings
from App.models import *
import requests
from sendbox_core.integrations.falcon_integration.headless_falcon_middleware import marshal


# @celery.task
# def send_sms(phone, sms, country_code, **kwargs):
#     if settings.DEV_SETTINGS:
#         phone = settings.DEV_PHONE
#     send_text(phone, sms, country_code, **kwargs)
#
#
# @celery.task
# def send_email(email, template_alias, data=None):
#     data = data if data else {}
#     if settings.DEV_SETTINGS:
#         email = settings.DEV_EMAIL
#         if data.get("cc"):
#             data['cc'] = settings.DEV_EMAIL_CC
#     email_sender(emails=[email], template_alias=template_alias, data=data)


@celery.task
def post_to_url(url, data, schema=None):
    """
    Send a post request
    @param url:
    @param data:
    @param schema:
    @return:
    """

    if schema:
        data = marshal(data, schema)

    pprint(data)
    print("teeeeeeeeeeeeeeeeeeeeeel", url)
    res = requests.post(url, json.dumps(data, default=str),
                        headers={"Content-Type": "application/json", "Accept": "application/json",
                                 "Method": "POST", "Cache-Control": "no-cache", "User-Agent": "python/sendbox-api"})
    try:
        print(res.json())
        return res.json()
    except Exception as e:
        print("invalid responnnnnnnnnnnnn", e)
        print(res.status_code)


@celery.task
def send_notification(code, instance_id, target, user_id, **kwargs):
    """
    make a rest call to the notification service to send out notifications
    @return:
    """
    data = kwargs
    print(data)
    payload = data.get("payload")
    email_recipients = data.get("email_recipients", [])
    sms_recipients = data.get("sms_recipients", [])
    push_recipients = data.get("push_recipients", [])
    webhook_recipients = data.get("webhook_recipients", [])
    subject_template = data.get("subject_template")

    url = settings.HEADLESS_NOTIFICATIONS_INTERNAL_BASE_URL + "/engine/send"

    body = {"code": code, "instance_id": instance_id,
            "target": target, "target_id": user_id,
            "payload": payload, "email_recipients": email_recipients,
            "sms_recipients": sms_recipients, "push_recipients": push_recipients,
            "webhook_recipients": webhook_recipients, "subject_template": subject_template}

    try:
        post_to_url(url, data=dict(request_data=body))
    except Exception as e:
        print(e, "error sending notification..................................................")


def notify_parties(code, payload, invoice_id, instance_id):
    """

    Parameters
    ----------
    instance_id
    code
    payload
    invoice_id

    Returns
    -------

    """
    from App.services.invoice import InvoiceService

    invoice = InvoiceService.get(invoice_id)
    merchant = invoice.user
    notification_data = dict(payload=payload)

    send_notification.delay(code=code + ".customer", instance_id=instance_id, target="instance",
                            user_id=instance_id, email_recipients=[invoice.customer.email], **notification_data)

    send_notification.delay(code=code + ".merchant", instance_id=instance_id, target="user",
                            user_id=merchant.user_id, email_recipients=[merchant.email],
                            **notification_data)


@celery.task
def do_reconciliation(invoice_id):
    """

    """
    from App.services.invoice import ReconciliationService
    print(invoice_id)
    ReconciliationService.register(invoice_id=invoice_id)
