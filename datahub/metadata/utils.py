from datahub.metadata.models import ExchangeRate


def convert_usd_to_gbp(usd):
    """convert_usd_to_gbp.

    :param usd: A numeric value in US Dollars
    :returns: A numeric value in GBP
    """
    exchange_rate = get_latest_exchange_rate()
    return usd * exchange_rate


def convert_gbp_to_usd(gbp):
    """convert_gbp_to_usd.

    :param gbp: A numeric value in British Pounds
    :returns: A numeric value in USD
    """
    exchange_rate = get_latest_exchange_rate()
    return gbp * (1 / exchange_rate)


def get_latest_exchange_rate():
    """get_latest_exchange_rate.

    :returns: A numeric value for latest USD to GBP exchange rate
    """
    return ExchangeRate.objects.filter(
        from_currency_code='USD',
        to_currency_code='GBP',
    ).order_by('-created_on').first().exchange_rate
