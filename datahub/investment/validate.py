from django.forms import model_to_dict

from datahub.core.constants import (
    InvestmentType, ReferralSourceActivity as Activity
)

REQUIRED_MESSAGE = 'This field is required.'


def get_incomplete_project_fields(instance=None, update_data=None):
    """Checks whether the project section is complete.

    :param instance:    Model instance (for update operations only)
    :param update_data: Data being updated
    :return:            dict containing errors for incomplete fields
    """
    if instance is None and update_data is None:
        raise TypeError('One of instance and update_data must be provided '
                        'and not None')

    if update_data is None:
        update_data = {}

    merged_data = model_to_dict(instance) if instance else {}
    merged_data.update(update_data)

    errors = {}
    truthy_required_fields = [
        'sector',
        'referral_source_advisor',
        'client_contacts',
        'client_relationship_manager',
        'business_activity',
        'investor_company',
        'referral_source_activity'
    ]

    if (_get_value_id(merged_data, 'referral_source_activity') ==
            Activity.event.value.id):
        truthy_required_fields.append('referral_source_activity_event')

    if (_get_value_id(merged_data, 'referral_source_activity') ==
            Activity.marketing.value.id):
        truthy_required_fields.append('referral_source_activity_marketing')

    if (_get_value_id(merged_data, 'referral_source_activity') ==
            Activity.website.value.id):
        truthy_required_fields.append('referral_source_activity_website')

    if (_get_value_id(merged_data, 'investment_type') ==
            InvestmentType.fdi.value.id):
        truthy_required_fields.append('fdi_type')

    if (_get_value_id(merged_data, 'investment_type') ==
            InvestmentType.non_fdi.value.id):
        truthy_required_fields.append('non_fdi_type')

    for field_name in truthy_required_fields:
        _validate_truthy(merged_data, field_name, errors)

    return errors


def _get_value(merged_data, field_name):
    return merged_data.get(field_name)


def _get_value_id(merged_data, field_name):
    value = _get_value(merged_data, field_name)
    return str(value) if value else None


def _validate_truthy(merged_data, field_name, errors):
    value = _get_value(merged_data, field_name)
    if not value:
        errors[field_name] = REQUIRED_MESSAGE


def _validate_string_or_number(merged_data, field_name, errors):
    value = _get_value(merged_data, field_name)
    if value not in (None, ''):
        errors[field_name] = REQUIRED_MESSAGE
