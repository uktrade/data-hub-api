from datahub.metadata.models import Country, ExchangeRate


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
    return (
        ExchangeRate.objects.filter(
            from_currency_code='USD',
            to_currency_code='GBP',
        )
        .order_by('-created_on')
        .first()
        .exchange_rate
    )


def get_country_by_country_name(name: str, default_iso='') -> Country:
    """Attempts to match a Country from the given name or by the given default_iso is match by name
    is not found.

    :param name: a country name
    :param default_iso: an ISO code to default to if there are no matches by name
    :returns: DataHub `Country`
    :raises Country.DoesNotExist: if Country is not found with given `name` and `default_iso` not
        given.
    :raises Country.DoesNotExist: if Country is not found with given `name` and then also not
        found with given `default_iso`
    """
    try:
        return Country.objects.get(name=name)
    except Country.DoesNotExist as error:
        if not default_iso:
            raise error

    return Country.objects.get(iso_alpha2_code=default_iso)
