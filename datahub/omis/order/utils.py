class _Address:
    MAPPING = {
        'line_1': '{prefix}_1',
        'line_2': '{prefix}_2',
        'town': '{prefix}_town',
        'county': '{prefix}_county',
        'postcode': '{prefix}_postcode',
        'country': '{prefix}_country',
    }

    def __init__(self, field_prefix, company):
        """
        Initialises the object from the company using the values from the fields
        with prefix `field_prefix`.
        """
        for attr_name, model_field_name_template in self.MAPPING.items():
            model_field_name = model_field_name_template.format(prefix=field_prefix)
            model_field_value = getattr(company, model_field_name)

            setattr(self, attr_name, model_field_value)

    def is_blank(self):
        """
        :returns: True if none of the field values are defined, False otherwise.
        """
        return not any(
            getattr(self, attr)
            for attr in self.MAPPING
        )


def compose_official_address(company):
    """
    :returns: the most official address for the given company as an object
    with the following properties:
        line_1
        line_2
        town
        county
        postcode
        country

    The values come from registered address if defined or from the address otherwise.
    """
    registered_address = _Address('registered_address', company)

    if not registered_address.is_blank():
        return registered_address

    return _Address('address', company)


def populate_billing_data(order):
    """
    Populate the order.billing_* fields from the company/contact if not set already.

    :param order: Order to change if needed
    :returns: order with billing_* fields filled in
    """
    company = order.company

    # get default and current order values of billing details
    default_billing_details = {
        'billing_company_name': company.name,
    }
    order_billing_details = {
        field_name: getattr(order, field_name)
        for field_name in default_billing_details
        if getattr(order, field_name)
    }

    company_address = compose_official_address(company)

    # get default and current order values of billing address
    default_billing_address = {
        'billing_address_1': company_address.line_1 or '',
        'billing_address_2': company_address.line_2 or '',
        'billing_address_town': company_address.town or '',
        'billing_address_county': company_address.county or '',
        'billing_address_postcode': company_address.postcode or '',
        'billing_address_country': company_address.country,
    }
    order_billing_address = {
        field_name: getattr(order, field_name)
        for field_name in default_billing_address
    }

    # compose the final data dict, default values are overridden
    data = {
        **default_billing_details,
        **order_billing_details,
        **(
            order_billing_address
            if any(order_billing_address.values())
            else default_billing_address
        ),
    }

    # set order fields
    for field_name, field_value in data.items():
        setattr(order, field_name, field_value)
