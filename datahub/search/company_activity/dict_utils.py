from datahub.search import dict_utils


def activity_interaction_dict(obj):
    """Creates a dictionary for an interaction."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'date': obj.date,
        'subject': obj.subject,
        'kind': obj.kind,
        'dit_participants': dict_utils.dit_participant_list(obj.dit_participants),
        'communication_channel': dict_utils.id_name_dict(obj.communication_channel),
        'contacts': dict_utils.contact_or_adviser_list_of_dicts(obj.contacts),
        'service': dict_utils.id_name_dict(obj.service),
    }


def activity_referral_dict(obj):
    """Creates a dictionary for a referral."""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'completed_on': obj.completed_on,
        'created_on': obj.created_on,
        'subject': obj.subject,
        'notes': obj.notes,
        'status': obj.status,
        'recipient': dict_utils.contact_or_adviser_dict(obj.recipient),
        'created_by': dict_utils.contact_or_adviser_dict(obj.created_by),
        'contact': dict_utils.contact_or_adviser_dict(obj.contact),
    }


def activity_investment_dict(obj):
    """Creates dictionary from an investment project containing id, name and investor company"""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'name': obj.name,
        'investment_type': dict_utils.id_name_dict(obj.investment_type),
        'estimated_land_date': obj.estimated_land_date,
        'total_investment': obj.total_investment,
        'foreign_equity_investment': obj.foreign_equity_investment,
        'gross_value_added': obj.gross_value_added,
        'number_new_jobs': obj.number_new_jobs,
        'created_by': dict_utils.contact_or_adviser_dict(obj.created_by),
        'client_contacts': dict_utils.contact_job_list_of_dicts(obj.client_contacts),
    }


def order_assignees_list(assignees_manager):
    return [
        {
            'adviser': dict_utils.contact_or_adviser_dict(assigneee.adviser),
            'team': dict_utils.id_name_dict(assigneee.team),
        }
        for assigneee in assignees_manager.all()
    ]


def activity_order_dict(obj):
    """Creates dictionary from an omis order"""
    if obj is None:
        return None

    return {
        'id': str(obj.id),
        'created_on': obj.created_on,
        'reference': obj.reference,
        'primary_market': dict_utils.id_name_dict(obj.primary_market),
        'uk_region': dict_utils.id_name_dict(obj.uk_region),
        'assignees': dict_utils.contact_or_adviser_dict(obj.assignees),
        'contact': dict_utils.contact_or_adviser_list_of_dicts(obj.contacts),
    }
