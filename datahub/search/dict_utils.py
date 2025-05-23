def _attrgetter_with_default(attr, default):
    """It returns a function that can be called with an object to get the value
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


def empty_string_to_null(obj):
    if not obj:
        return None
    return obj


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
    """Creates a dictionary for the address fields with the given prefix
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
        'area': lambda obj: id_name_dict(
            getattr(obj, f'{prefix}_area'),
        ),
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


def contact_job_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    if obj is None:
        return None

    data = {
        'id': str(obj.id),
        'first_name': obj.first_name,
        'last_name': obj.last_name,
        'name': obj.name,
        'job_title': obj.job_title,
    }
    return data


def core_team_advisers_list_of_dicts(list_of_obj):
    """Creates a list of dicts for company advisers if they are
    not global account managers.
    """
    if list_of_obj is None:
        return None
    return [
        contact_or_adviser_dict(obj['adviser'])
        for obj in list_of_obj
        if not obj['is_global_account_manager']
    ]


def contact_or_adviser_list_of_dicts(manager):
    """Creates a list of dicts from a manager for contacts or advisers."""
    return _list_of_dicts(contact_or_adviser_dict, manager)


def contact_job_list_of_dicts(manager):
    """Creates a list of dicts from a manager for contacts or advisers."""
    return _list_of_dicts(contact_job_dict, manager)


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


def task_company(obj):
    """Creates dictionary from a task company containing id and name."""
    company = obj.get_company()
    if company is None:
        return None

    return id_name_dict(company)


def task_investment_project_dict(obj):
    """Creates dictionary from a task investment project containing id, name and project_code."""
    if not hasattr(obj, 'investment_project'):
        return None

    return investment_project_dict(obj.investment_project)


def task_interaction_dict(obj):
    """Creates dictionary from a task interaction containing id, subject and date."""
    if not hasattr(obj, 'interaction'):
        return None

    return interaction_dict(obj.interaction)


def sector_dict(obj):
    """Creates a dictionary for a sector."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'name': obj.name,
        'ancestors': [
            {
                'id': str(ancestor.id),
            }
            for ancestor in obj.get_ancestors()
        ],
    }


def interaction_dict(obj):
    """Creates a dictionary for an interaction."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'date': obj.date,
        'subject': obj.subject,
    }


def _list_of_dicts(dict_factory, manager):
    """Creates a list of dicts with ID and name keys from a manager."""
    return [dict_factory(obj) for obj in manager.all()]


def nested_company_global_account_manager(obj, company_prop_name):
    field = getattr(obj, company_prop_name, None)
    if field is None:
        return None
    return contact_or_adviser_dict(field.get_one_list_group_global_account_manager())


def dit_participant_list(dit_participant_manager):
    return [
        {
            'adviser': contact_or_adviser_dict(dit_participant.adviser),
            'team': id_name_dict(dit_participant.team),
        }
        for dit_participant in dit_participant_manager.all()
    ]


def eyb_lead_list(eyb_lead_list):
    return [
        {
            'id': str(eyb_lead.id),
            'company_name': eyb_lead.company_name,
            'created_on': eyb_lead.created_on,
            'triage_created': eyb_lead.triage_created,
            'is_high_value': eyb_lead.is_high_value,
        }
        for eyb_lead in eyb_lead_list.all()
    ]
