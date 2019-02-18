from datahub.search import dict_utils


def computed_address_field(field):
    """Gets Contact address from Company is address_same_as_company."""
    def get_field(contact):
        obj = contact.company if contact.address_same_as_company else contact
        value = getattr(obj, field)

        if field == 'address_country':
            return dict_utils.id_name_dict(value)

        return value

    return get_field
