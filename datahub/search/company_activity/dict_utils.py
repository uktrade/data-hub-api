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
