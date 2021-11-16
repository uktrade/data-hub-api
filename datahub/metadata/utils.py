from datahub.metadata.models import ExchangeRate


def convert_usd_to_gbp(usd):
    """convert_usd_to_gbp.

    :param usd: A numeric value in US Dollars
    :returns: A numeric value in GBP
    """
    exchange_rate = ExchangeRate.objects.filter(
        from_currency_code='USD',
        to_currency_code='GBP',
    ).order_by('-created_on').first()
    return usd * exchange_rate.exchange_rate


def convert_gbp_to_usd(gbp):
    """convert_gbp_to_usd.

    :param gbp: A numeric value in Bristish Pounds
    :returns: A numeric value in USD
    """
    exchange_rate = ExchangeRate.objects.filter(
        from_currency_code='GBP',
        to_currency_code='USD',
    ).order_by('-created_on').first().exchange_rate

    return gbp * exchange_rate
