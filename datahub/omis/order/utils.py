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

    # get default and current order values of billing address
    default_billing_address = {
        'billing_address_1': company.registered_address_1 or '',
        'billing_address_2': company.registered_address_2 or '',
        'billing_address_town': company.registered_address_town or '',
        'billing_address_county': company.registered_address_county or '',
        'billing_address_postcode': company.registered_address_postcode or '',
        'billing_address_country': company.registered_address_country,
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
