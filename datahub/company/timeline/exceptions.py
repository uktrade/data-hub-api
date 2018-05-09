from datahub.core.exceptions import DataHubException


class InvalidCompanyNumberError(DataHubException):
    """
    An invalid company number was provided.

    This includes blank company numbers, or company numbers containing only zeroes.
    """
