# coding=utf-8
from sendbox_core.integrations.falcon_integration.errors import SendboxHTTPError


class Unauthorized(SendboxHTTPError):
    """
    The generic http error that can be thrown from within a falcon app
    """

    def __init__(self, data=None, code=None):
        """
        the initialization
        :param data:
        """
        self.data = data
        self.status = "401 "
        self.code = code
        super(Unauthorized, self).__init__(self.status, data=data)
