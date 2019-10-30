def _attrgetter_with_default(attr, default):
    """
    It returns a function that can be called with an object to get the value
    of attr or the default.
    Useful to convert None values to ''.
    """
    def _getter(obj):
        return getattr(obj, attr) or default
    return _getter


def id_name_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'name': obj.name,
    }


def id_name_list_of_dicts(manager):
    """Creates a list of dicts with ID and name keys from a manager."""
    return _list_of_dicts(id_name_dict, manager)


def id_type_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'type': obj.type,
    }


def id_uri_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'uri': obj.uri,
    }


def address_dict(obj, prefix='address'):
    """
    Creates a dictionary for the address fields with the given prefix
    to be used as nested object.
    """
    if obj is None:
        return None

    mapping = {
        'line_1': _attrgetter_with_default(f'{prefix}_1', ''),
        'line_2': _attrgetter_with_default(f'{prefix}_2', ''),
        'town': _attrgetter_with_default(f'{prefix}_town', ''),
        'county': _attrgetter_with_default(f'{prefix}_county', ''),
        'postcode': _attrgetter_with_default(f'{prefix}_postcode', ''),
        'country': lambda obj: id_name_dict(
            getattr(obj, f'{prefix}_country'),
        ),
    }

    address = {
        target_source_name: value_getter(obj)
        for target_source_name, value_getter in mapping.items()
    }

    if any(address.values()):
        return address
    return None


def company_dict(obj):
    """Creates dictionary for a company field."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'name': obj.name,
        'trading_names': obj.trading_names,
    }


def contact_or_adviser_dict(obj, include_dit_team=False):
    """Creates dictionary with selected field from supplied object."""
    if obj is None:
        return None

    data = {
        'id': str(obj.id),
        'first_name': obj.first_name,
        'last_name': obj.last_name,
        'name': obj.name,
    }

    if include_dit_team:
        if obj.dit_team:
            data['dit_team'] = id_name_dict(obj.dit_team)
        else:
            data['dit_team'] = {}
    return data


def contact_or_adviser_list_of_dicts(manager):
    """Creates a list of dicts from a manager for contacts or advisers."""
    return _list_of_dicts(contact_or_adviser_dict, manager)


def adviser_dict_with_team(obj):
    """Creates a dictionary with adviser names fields and the adviser's team."""
    return contact_or_adviser_dict(obj, include_dit_team=True)


def _computed_nested_dict(nested_field, dict_func):
    """Creates a dictionary from a nested field using dict_func."""
    def get_dict(obj):
        fields = nested_field.split('.', maxsplit=1)
        if len(fields) != 2:
            raise ValueError("nested_field must be in 'nested_object.nested_field' format.")

        related_object = getattr(obj, fields[0])
        if related_object is None:
            return None

        field = getattr(related_object, fields[1])
        if field is None:
            return None

        return dict_func(field)

    return get_dict


def computed_field_function(function_name, dict_func):
    """Create a dictionary from a result of provided function call."""
    def get_dict(obj):
        field = getattr(obj, function_name, None)
        if field is None:
            raise ValueError(f'The object function "{function_name}" does not exist.')
        if not callable(field):
            raise ValueError(f'"{function_name}" is not callable.')

        return dict_func(field())

    return get_dict


def computed_nested_id_name_dict(nested_field):
    """Creates a dictionary with id and name from a nested field."""
    return _computed_nested_dict(nested_field, id_name_dict)


def computed_nested_sector_dict(nested_field):
    """Creates a dictionary for a sector from from a nested field."""
    return _computed_nested_dict(nested_field, sector_dict)


def ch_company_dict(obj):
    """Creates dictionary from a company with id and company_number keys."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'company_number': obj.company_number,
    }


def investment_project_dict(obj):
    """Creates dictionary from an investment project containing id, name and project_code."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'name': obj.name,
        'project_code': obj.project_code,
    }


def sector_dict(obj):
    """Creates a dictionary for a sector."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'name': obj.name,
        'ancestors': [{
            'id': str(ancestor.id),
        } for ancestor in obj.get_ancestors()],
    }


def _list_of_dicts(dict_factory, manager):
    """Creates a list of dicts with ID and name keys from a manager."""
    return [dict_factory(obj) for obj in manager.all()]
