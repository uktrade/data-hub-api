from collections import namedtuple

from rest_framework.utils import model_meta


from datahub.core.constants import (
    InvestmentProjectPhase as Phase, InvestmentType,
    ReferralSourceActivity as Activity
)
from datahub.core.validate_utils import UpdatedDataView
from datahub.investment.models import InvestmentProject


def is_falsey(val):
    """Returns True if val if bool(val) is False"""
    return not val


REQUIRED_MESSAGE = 'This field is required.'

VALIDATION_MAPPING = {
    'client_cannot_provide_total_investment': Phase.assign_pm.value,
    'number_new_jobs': Phase.assign_pm.value,
    'strategic_drivers': Phase.assign_pm.value,
    'uk_region_locations': Phase.assign_pm.value,
    'client_requirements': Phase.assign_pm.value,
    'client_considering_other_countries': Phase.assign_pm.value,
    'site_decided': Phase.assign_pm.value,
    'project_manager': Phase.active.value,
    'project_assurance_adviser': Phase.active.value,
}

CondValRule = namedtuple('CondValRule', ('field', 'value', 'phase'))

CONDITIONAL_VALIDATION_MAPPING = {
    'referral_source_activity_event':
        CondValRule('referral_source_activity', Activity.event.value.id, Phase.prospect.value),
    'referral_source_activity_marketing':
        CondValRule('referral_source_activity', Activity.marketing.value.id, Phase.prospect.value),
    'referral_source_activity_website':
        CondValRule('referral_source_activity', Activity.website.value.id, Phase.prospect.value),
    'fdi_type':
        CondValRule('investment_type', InvestmentType.fdi.value.id, Phase.prospect.value),
    'non_fdi_type':
        CondValRule('investment_type', InvestmentType.non_fdi.value.id, Phase.prospect.value),
    'total_investment':
        CondValRule('client_cannot_provide_total_investment', is_falsey, Phase.assign_pm.value),
    'competitor_countries':
        CondValRule('client_considering_other_countries', True, Phase.assign_pm.value)
}


def validate(instance=None, update_data=None, fields=None, next_phase=False):
    """Validates an investment project for the current phase.

    :param instance:    Model instance (for update operations only)
    :param update_data: Data being updated
    :param fields:      Fields to restrict validation to
    :param next_phase:  Perform validation for the next phase
    :return:            dict containing errors for incomplete fields
    """
    data = UpdatedDataView(instance, update_data)
    info = model_meta.get_field_info(InvestmentProject)
    desired_phase = data.get_value('phase') or Phase.prospect.value
    desired_phase_order = desired_phase.order
    if next_phase:
        desired_phase_order += 100.0

    errors = {}

    for field, req_phase in VALIDATION_MAPPING.items():
        if fields is not None and field not in fields:
            continue

        if desired_phase_order < req_phase.order:
            continue

        if _field_incomplete(info, data, field):
            errors[field] = REQUIRED_MESSAGE

    for field, rule in CONDITIONAL_VALIDATION_MAPPING.items():
        if fields is not None and field not in fields:
            continue

        if desired_phase_order < rule.phase.order:
            continue

        if _compare_value(info, data, rule) and _field_incomplete(info, data, field):
            errors[field] = REQUIRED_MESSAGE

    return errors


def _field_incomplete(field_info, data_view, field):
    if field in field_info.relations and field_info.relations[field].to_many:
        return not data_view.get_value_to_many(field)
    return data_view.get_value(field) in (None, '')


def _compare_value(field_info, data_view, rule):
    if rule.field in field_info.relations:
        actual_value = data_view.get_value_id(rule.field)
    else:
        actual_value = data_view.get_value(rule.field)
    if callable(rule.value):
        return rule.value(actual_value)
    return actual_value == rule.value


def get_validators():
    """Returns validators used for phase-dependent validation.

    Returned as a tuple of (phase, callable) pairs.
    """
    return (
        (Phase.prospect.value, get_incomplete_prospect_project_fields),
        (Phase.assign_pm.value, get_incomplete_assign_pm_value_fields),
        (Phase.assign_pm.value, get_incomplete_assign_pm_reqs_fields),
        (Phase.active.value, get_incomplete_active_team_fields)
    )


def get_incomplete_prospect_project_fields(instance=None, update_data=None):
    """Checks whether the project section is complete.

    :param instance:    Model instance (for update operations only)
    :param update_data: Data being updated
    :return:            dict containing errors for incomplete fields
    """
    data = UpdatedDataView(instance, update_data)

    truthy_required_fields = []

    if data.get_value_id('referral_source_activity') == Activity.event.value.id:
        truthy_required_fields.append('referral_source_activity_event')

    if data.get_value_id('referral_source_activity') == Activity.marketing.value.id:
        truthy_required_fields.append('referral_source_activity_marketing')

    if data.get_value_id('referral_source_activity') == Activity.website.value.id:
        truthy_required_fields.append('referral_source_activity_website')

    if data.get_value_id('investment_type') == InvestmentType.fdi.value.id:
        truthy_required_fields.append('fdi_type')

    if data.get_value_id('investment_type') == InvestmentType.non_fdi.value.id:
        truthy_required_fields.append('non_fdi_type')

    errors = _validate(data, truthy_required_fields)
    return errors


def get_incomplete_assign_pm_value_fields(instance=None, update_data=None):
    """Checks whether the value section is complete.

    :param instance:    Model instance (for update operations only)
    :param update_data: Data being updated
    :return:            dict containing errors for incomplete fields
    """
    data = UpdatedDataView(instance, update_data)

    truthy_required_fields = []
    not_none_or_blank_fields = [
        'client_cannot_provide_total_investment',
        'number_new_jobs',
    ]

    if not data.get_value('client_cannot_provide_total_investment'):
        not_none_or_blank_fields.append('total_investment')

    errors = _validate(data, truthy_required_fields, not_none_or_blank_fields)
    return errors


def get_incomplete_assign_pm_reqs_fields(instance=None, update_data=None):
    """Checks whether the requirements section is complete.

    :param instance:    Model instance (for update operations only)
    :param update_data: Data being updated
    :return:            dict containing errors for incomplete fields
    """
    data = UpdatedDataView(instance, update_data)

    to_many_required_fields = [
        'strategic_drivers',
        'uk_region_locations'
    ]
    not_none_or_blank_fields = [
        'client_requirements',
        'client_considering_other_countries',
        'uk_region_locations',
        'site_decided'
    ]

    if data.get_value('client_considering_other_countries'):
        to_many_required_fields.append('competitor_countries')

    errors = _validate(
        data, not_none_or_blank_fields=not_none_or_blank_fields,
        to_many_fields=to_many_required_fields
    )
    return errors


def get_incomplete_active_team_fields(instance=None, update_data=None):
    """Checks whether the team section is complete.

    :param instance:    Model instance (for update operations only)
    :param update_data: Data being updated
    :return:            dict containing errors for incomplete fields
    """
    data = UpdatedDataView(instance, update_data)

    truthy_required_fields = [
        'project_manager',
        'project_assurance_adviser'
    ]

    errors = _validate(data, truthy_required_fields)
    return errors


def _validate(data, truthy_fields=None, not_none_or_blank_fields=None, to_many_fields=None):
    errors = {}

    for field_name in truthy_fields or ():
        _validate_truthy(data.get_value(field_name), field_name, errors)

    for field_name in not_none_or_blank_fields or ():
        _validate_not_none_or_blank(data.get_value(field_name), field_name, errors)

    for field_name in to_many_fields or ():
        _validate_truthy(data.get_value_to_many(field_name), field_name, errors)

    return errors


def _validate_truthy(value, field_name, errors):
    if not value:
        errors[field_name] = REQUIRED_MESSAGE


def _validate_not_none_or_blank(value, field_name, errors):
    if value in (None, ''):
        errors[field_name] = REQUIRED_MESSAGE
