# coding=utf-8
"""
users.py
@Author: Jason Nwakaeze
@Date: August 25, 2021
"""
from .invoice import InvoiceService
from .profile import InstanceService, ProfileService, EntityService


class BaseInvoicingBackendService:

    def __init__(self):
        """"""

        self.profile_service = ProfileService
        self.invoice_service = InvoiceService
        self.instance_service = InstanceService
        self.entity_service = EntityService


InvoicingBackendService = BaseInvoicingBackendService()
