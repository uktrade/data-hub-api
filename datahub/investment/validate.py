from collections import namedtuple

from rest_framework.utils import model_meta

from datahub.core.constants import (
    InvestmentProjectPhase as Phase, InvestmentType,
    ReferralSourceActivity as Activity
)
from datahub.core.utils import is_falsey
from datahub.core.validate_utils import UpdatedDataView
from datahub.investment.models import InvestmentProject


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
    'total_investment': Phase.verify_win.value,
    'government_assistance': Phase.verify_win.value,
    'number_safeguarded_jobs': Phase.verify_win.value,
    'r_and_d_budget': Phase.verify_win.value,
    'non_fdi_r_and_d_budget': Phase.verify_win.value,
    'new_tech_to_uk': Phase.verify_win.value,
    'export_revenue': Phase.verify_win.value,
    'address_line_1': Phase.verify_win.value,
    'address_line_2': Phase.verify_win.value,
    'address_line_postcode': Phase.verify_win.value,
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
        CondValRule('client_considering_other_countries', True, Phase.assign_pm.value),
    'average_salary':
        CondValRule('number_new_jobs', bool, Phase.verify_win.value),
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
        if _should_skip_rule(field, fields, desired_phase_order, req_phase.order):
            continue

        if _field_incomplete(info, data, field):
            errors[field] = REQUIRED_MESSAGE

    for field, rule in CONDITIONAL_VALIDATION_MAPPING.items():
        if _should_skip_rule(field, fields, desired_phase_order, rule.phase.order):
            continue

        if _compare_value(info, data, rule) and _field_incomplete(info, data, field):
            errors[field] = REQUIRED_MESSAGE

    return errors


def _should_skip_rule(field, validate_fields, desired_phase_order, req_phase_order):
    skip_field = validate_fields is not None and field not in validate_fields

    return skip_field or desired_phase_order < req_phase_order


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
