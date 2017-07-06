"""Performs stage-dependent validation on investment projects."""
from collections import namedtuple
from operator import not_

from rest_framework.utils import model_meta

from datahub.core.constants import (
    InvestmentProjectStage as Stage, InvestmentType,
    ReferralSourceActivity as Activity
)
from datahub.core.validate_utils import UpdatedDataView
from datahub.investment.models import InvestmentProject


REQUIRED_MESSAGE = 'This field is required.'

# Mapping from field name to the stage the field becomes required.
VALIDATION_MAPPING = {
    'client_cannot_provide_total_investment': Stage.assign_pm.value,
    'number_new_jobs': Stage.assign_pm.value,
    'strategic_drivers': Stage.assign_pm.value,
    'uk_region_locations': Stage.assign_pm.value,
    'client_requirements': Stage.assign_pm.value,
    'client_considering_other_countries': Stage.assign_pm.value,
    'site_decided': Stage.assign_pm.value,
    'project_manager': Stage.active.value,
    'project_assurance_adviser': Stage.active.value,
    'client_cannot_provide_foreign_investment': Stage.verify_win.value,
    'government_assistance': Stage.verify_win.value,
    'number_safeguarded_jobs': Stage.verify_win.value,
    'r_and_d_budget': Stage.verify_win.value,
    'non_fdi_r_and_d_budget': Stage.verify_win.value,
    'new_tech_to_uk': Stage.verify_win.value,
    'export_revenue': Stage.verify_win.value,
    'address_line_1': Stage.verify_win.value,
    'address_line_2': Stage.verify_win.value,
    'address_line_postcode': Stage.verify_win.value,
}

CondValRule = namedtuple('CondValRule', ('field', 'condition', 'stage'))

# Conditional validation rules. Mapping from field names to validation rules.
CONDITIONAL_VALIDATION_MAPPING = {
    'referral_source_activity_event':
        CondValRule('referral_source_activity', Activity.event.value.id, Stage.prospect.value),
    'referral_source_activity_marketing':
        CondValRule('referral_source_activity', Activity.marketing.value.id, Stage.prospect.value),
    'referral_source_activity_website':
        CondValRule('referral_source_activity', Activity.website.value.id, Stage.prospect.value),
    'fdi_type':
        CondValRule('investment_type', InvestmentType.fdi.value.id, Stage.prospect.value),
    'non_fdi_type':
        CondValRule('investment_type', InvestmentType.non_fdi.value.id, Stage.prospect.value),
    'total_investment':
        CondValRule('client_cannot_provide_total_investment', not_, Stage.assign_pm.value),
    'competitor_countries':
        CondValRule('client_considering_other_countries', True, Stage.assign_pm.value),
    'foreign_equity_investment':
        CondValRule('client_cannot_provide_foreign_investment', not_, Stage.verify_win.value),
    'average_salary':
        CondValRule('number_new_jobs', bool, Stage.verify_win.value),
}


def validate(instance=None, update_data=None, fields=None, next_stage=False):
    """Validates an investment project for the current stage.

    :param instance:    Model instance (for update operations only)
    :param update_data: New data to update or create the instance with
    :param fields:      Fields to restrict validation to
    :param next_stage:  Perform validation for the next stage (rather than the current stage)
    :return:            dict containing errors for incomplete fields
    """
    data = UpdatedDataView(instance, update_data)
    info = model_meta.get_field_info(InvestmentProject)
    desired_stage = data.get_value('stage') or Stage.prospect.value
    desired_stage_order = desired_stage.order
    if next_stage:
        desired_stage_order += 100.0

    errors = {}

    for field, req_stage in VALIDATION_MAPPING.items():
        if _should_skip_rule(field, fields, desired_stage_order, req_stage.order):
            continue

        if _field_incomplete(info, data, field):
            errors[field] = REQUIRED_MESSAGE

    for field, rule in CONDITIONAL_VALIDATION_MAPPING.items():
        if _should_skip_rule(field, fields, desired_stage_order, rule.stage.order):
            continue

        if _check_rule(info, data, rule) and _field_incomplete(info, data, field):
            errors[field] = REQUIRED_MESSAGE

    return errors


def _should_skip_rule(field, validate_fields, desired_stage_order, req_stage_order):
    """Whether a validation rule for a field should be skipped."""
    skip_field = validate_fields is not None and field not in validate_fields

    return skip_field or desired_stage_order < req_stage_order


def _field_incomplete(field_info, data_view, field):
    """Checks whether a field has been completed."""
    if field in field_info.relations and field_info.relations[field].to_many:
        return not data_view.get_value_to_many(field)
    return data_view.get_value(field) in (None, '')


def _check_rule(field_info, data_view, rule):
    """Checks a conditional validation rule."""
    if rule.field in field_info.relations and not field_info.relations[rule.field].to_many:
        actual_value = data_view.get_value_id(rule.field)
    else:
        actual_value = data_view.get_value(rule.field)
    if callable(rule.condition):
        return rule.condition(actual_value)
    return actual_value == rule.condition
