from django.forms import model_to_dict


def model_to_dict_company(obj):
    """
    Returns the dict representation of the given model object
    minus website and registered_address fields
    """
    field_to_filter = (
        'registered_address_1',
        'registered_address_2',
        'registered_address_town',
        'registered_address_county',
        'registered_address_country',
        'registered_address_postcode',
        'website',
    )
    return {
        field: value
        for field, value in model_to_dict(obj).items()
        if field not in field_to_filter
    }
