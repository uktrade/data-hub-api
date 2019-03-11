"""Performs stage-dependent validation on investment projects."""
from collections import namedtuple
from functools import partial
from operator import not_
from uuid import UUID

from datahub.core.constants import (
    InvestmentBusinessActivity as BusinessActivity,
    InvestmentProjectStage as Stage,
    InvestmentType,
    ReferralSourceActivity as Activity,
)
from datahub.core.validate_utils import DataCombiner
from datahub.feature_flag.utils import is_feature_flag_active
from datahub.investment.project.constants import FEATURE_FLAG_STREAMLINED_FLOW
from datahub.investment.project.models import InvestmentProject
from datahub.investment.validate import field_incomplete

REQUIRED_MESSAGE = 'This field is required.'

CondValRule = namedtuple('CondValRule', ('field', 'condition', 'stage'))


def _contains_id(id_, instances):
    # For updates the UUID is still a string
    if not isinstance(id_, UUID):
        id_ = UUID(id_)
    return any(_get_to_many_id(instance) == id_ for instance in instances)


def _get_to_many_id(instance):
    # For updates the UUID is still a string
    if isinstance(instance, str):
        return UUID(instance)
    return instance.id


class InvestmentProjectStageValidationConfig:
    """Investment Project stage validation config."""

    def __init__(self):
        """Checking feature flags that alter validation mapping."""
        self.is_streamlined_flow = is_feature_flag_active(FEATURE_FLAG_STREAMLINED_FLOW)

    def _get_next_stage_for_prospect(self):
        if self.is_streamlined_flow:
            return Stage.active.value
        return Stage.assign_pm.value

    def get_required_fields_after_stage(self):
        """Mapping from field name to the stage the field becomes required."""
        next_stage_for_prospect = self._get_next_stage_for_prospect()
        return {
            'client_cannot_provide_total_investment': next_stage_for_prospect,
            'number_new_jobs': next_stage_for_prospect,
            'strategic_drivers': next_stage_for_prospect,
            'client_requirements': next_stage_for_prospect,
            'client_considering_other_countries': next_stage_for_prospect,
            'project_manager': Stage.active.value,
            'project_assurance_adviser': Stage.active.value,
            'client_cannot_provide_foreign_investment': Stage.verify_win.value,
            'government_assistance': Stage.verify_win.value,
            'number_safeguarded_jobs': Stage.verify_win.value,
            'r_and_d_budget': Stage.verify_win.value,
            'non_fdi_r_and_d_budget': Stage.verify_win.value,
            'new_tech_to_uk': Stage.verify_win.value,
            'export_revenue': Stage.verify_win.value,
            'address_1': Stage.verify_win.value,
            'address_town': Stage.verify_win.value,
            'address_postcode': Stage.verify_win.value,
            'actual_uk_regions': Stage.verify_win.value,
            'delivery_partners': Stage.verify_win.value,
            'actual_land_date': Stage.won.value,
        }

    def get_conditional_rules_after_stage(self):
        """Conditional validation rules. Mapping from field names to validation rules."""
        next_stage_for_prospect = self._get_next_stage_for_prospect()
        return {
            'referral_source_activity_event':
                CondValRule(
                    'referral_source_activity', Activity.event.value.id, Stage.prospect.value,
                ),
            'other_business_activity':
                CondValRule(
                    'business_activities',
                    partial(_contains_id, BusinessActivity.other.value.id),
                    Stage.prospect.value,
                ),
            'referral_source_activity_marketing':
                CondValRule(
                    'referral_source_activity', Activity.marketing.value.id, Stage.prospect.value,
                ),
            'referral_source_activity_website':
                CondValRule(
                    'referral_source_activity', Activity.website.value.id, Stage.prospect.value,
                ),
            'fdi_type':
                CondValRule(
                    'investment_type', InvestmentType.fdi.value.id, Stage.prospect.value,
                ),
            'total_investment':
                CondValRule(
                    'client_cannot_provide_total_investment', not_, next_stage_for_prospect,
                ),
            'competitor_countries':
                CondValRule(
                    'client_considering_other_countries', True, next_stage_for_prospect,
                ),
            'uk_region_locations':
                CondValRule(
                    'allow_blank_possible_uk_regions', False, next_stage_for_prospect,
                ),
            'foreign_equity_investment':
                CondValRule(
                    'client_cannot_provide_foreign_investment', not_, Stage.verify_win.value,
                ),
            'average_salary':
                CondValRule('number_new_jobs', bool, Stage.verify_win.value),
            'associated_non_fdi_r_and_d_project':
                CondValRule('non_fdi_r_and_d_budget', bool, Stage.verify_win.value),
        }


def validate(instance=None, update_data=None, fields=None, next_stage=False):
    """Validates an investment project for the current stage.

    :param instance:    Model instance (for update operations only)
    :param update_data: New data to update or create the instance with
    :param fields:      Fields to restrict validation to
    :param next_stage:  Perform validation for the next stage (rather than the current stage)
    :return:            dict containing errors for incomplete fields
    """
    combiner = DataCombiner(instance, update_data, model=InvestmentProject)
    desired_stage = combiner.get_value('stage') or Stage.prospect.value
    desired_stage_order = _get_desired_stage_order(desired_stage, next_stage)

    errors = {}
    validation_config = InvestmentProjectStageValidationConfig()

    for field, req_stage in validation_config.get_required_fields_after_stage().items():
        if _should_skip_rule(field, fields, desired_stage_order, req_stage.order):
            continue

        if field_incomplete(combiner, field):
            errors[field] = REQUIRED_MESSAGE

    for field, rule in validation_config.get_conditional_rules_after_stage().items():
        if _should_skip_rule(field, fields, desired_stage_order, rule.stage.order):
            continue

        if _check_rule(combiner, rule) and field_incomplete(combiner, field):
            errors[field] = REQUIRED_MESSAGE

    return errors


def _should_skip_rule(field, validate_fields, desired_stage_order, req_stage_order):
    """Whether a validation rule for a field should be skipped."""
    skip_field = validate_fields is not None and field not in validate_fields

    return skip_field or desired_stage_order < req_stage_order


def _check_rule(combiner, rule):
    """Checks a conditional validation rule."""
    value = combiner.get_value_auto(rule.field)
    if callable(rule.condition):
        return rule.condition(value)
    return value == rule.condition


def _get_desired_stage_order(desired_stage, next_stage):
    if not next_stage:
        return desired_stage.order

    is_streamlined_flow_active = is_feature_flag_active(FEATURE_FLAG_STREAMLINED_FLOW)

    if is_streamlined_flow_active and str(desired_stage.id) == Stage.prospect.value.id:
        return desired_stage.order + 200.0

    return desired_stage.order + 100.0
