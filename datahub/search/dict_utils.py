def id_name_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'name': obj.name,
    }


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


def company_dict(obj):
    """Creates dictionary for a company field."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'name': obj.name,
        'trading_name': obj.alias,
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
