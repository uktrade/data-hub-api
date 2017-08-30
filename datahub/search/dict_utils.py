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
        'type': obj.type
    }


def id_uri_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'uri': obj.uri
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


def computed_nested_id_name_dict(nested_field):
    """Creates dictionary with selected fields from nested_field."""
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

        return id_name_dict(field)

    return get_dict


def company_dict(obj):
    """Creates dictionary from a company with id and company_number keys."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'company_number': obj.company_number,
    }
