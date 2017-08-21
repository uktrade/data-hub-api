def _id_name_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    return {
        'id': str(obj.id),
        'name': obj.name,
    }


def _id_type_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    return {
        'id': str(obj.id),
        'type': obj.type
    }


def _id_uri_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    return {
        'id': str(obj.id),
        'uri': obj.uri
    }


def _contact_dict(obj, include_dit_team=False):
    """Creates dictionary with selected field from supplied object."""
    data = {
        'id': str(obj.id),
        'first_name': obj.first_name,
        'last_name': obj.last_name,
        'name': obj.name,
    }

    if include_dit_team:
        if obj.dit_team:
            data['dit_team'] = _id_name_dict(obj.dit_team)
        else:
            data['dit_team'] = {}
    return data


def _company_dict(obj):
    return {
        'id': str(obj.id),
        'company_number': obj.company_number,
    }
