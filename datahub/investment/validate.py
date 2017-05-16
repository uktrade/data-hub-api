from datahub.core.constants import (
    InvestmentType, InvestmentProjectPhase as Phase,
    ReferralSourceActivity as Activity
)

REQUIRED_MESSAGE = 'This field is required.'


def get_validators():
    """Returns a tuple of validators for phase-dependent validation."""
    return (
        (Phase.assign_pm.value, get_incomplete_project_fields),
        (Phase.assign_pm.value, get_incomplete_value_fields),
        (Phase.assign_pm.value, get_incomplete_reqs_fields),
        (Phase.active.value, get_incomplete_team_fields)
    )


def get_incomplete_project_fields(instance=None, update_data=None):
    """Checks whether the project section is complete.

    :param instance:    Model instance (for update operations only)
    :param update_data: Data being updated
    :return:            dict containing errors for incomplete fields
    """
    data = _UpdatedDataView(instance, update_data)

    truthy_required_fields = [
        'sector',
        'referral_source_advisor',
        'client_relationship_manager',
        'investor_company',
        'referral_source_activity'
    ]

    to_many_required_fields = [
        'client_contacts',
        'business_activities'
    ]

    if (data.get_value_id('referral_source_activity') ==
            Activity.event.value.id):
        truthy_required_fields.append('referral_source_activity_event')

    if (data.get_value_id('referral_source_activity') ==
            Activity.marketing.value.id):
        truthy_required_fields.append('referral_source_activity_marketing')

    if (data.get_value_id('referral_source_activity') ==
            Activity.website.value.id):
        truthy_required_fields.append('referral_source_activity_website')

    if data.get_value_id('investment_type') == InvestmentType.fdi.value.id:
        truthy_required_fields.append('fdi_type')

    if data.get_value_id('investment_type') == InvestmentType.non_fdi.value.id:
        truthy_required_fields.append('non_fdi_type')

    errors = _validate(data, truthy_required_fields,
                       to_many_fields=to_many_required_fields)
    return errors


def get_incomplete_value_fields(instance=None, update_data=None):
    """Checks whether the value section is complete.

    :param instance:    Model instance (for update operations only)
    :param update_data: Data being updated
    :return:            dict containing errors for incomplete fields
    """
    data = _UpdatedDataView(instance, update_data)

    truthy_required_fields = []
    not_none_or_blank_fields = [
        'client_cannot_provide_total_investment',
        'client_cannot_provide_foreign_investment',
        'total_investment',
        'foreign_equity_investment',
        'government_assistance',
        'number_new_jobs',
        'number_safeguarded_jobs',
        'r_and_d_budget',
        'non_fdi_r_and_d_budget',
        'new_tech_to_uk',
        'export_revenue',
    ]

    if data.get_value('client_cannot_provide_total_investment') is False:
        not_none_or_blank_fields.append('total_investment')

    if data.get_value('client_cannot_provide_foreign_investment') is False:
        not_none_or_blank_fields.append('foreign_equity_investment')

    num_new_jobs = data.get_value('number_new_jobs')
    if num_new_jobs is not None and num_new_jobs > 0:
        truthy_required_fields.append('average_salary')

    errors = _validate(data, truthy_required_fields, not_none_or_blank_fields)
    return errors


def get_incomplete_reqs_fields(instance=None, update_data=None):
    """Checks whether the requirements section is complete.

    :param instance:    Model instance (for update operations only)
    :param update_data: Data being updated
    :return:            dict containing errors for incomplete fields
    """
    data = _UpdatedDataView(instance, update_data)

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


def get_incomplete_team_fields(instance=None, update_data=None):
    """Checks whether the team section is complete.

    :param instance:    Model instance (for update operations only)
    :param update_data: Data being updated
    :return:            dict containing errors for incomplete fields
    """
    data = _UpdatedDataView(instance, update_data)

    truthy_required_fields = [
        'project_manager',
        'project_assurance_advisor'
    ]

    errors = _validate(data, truthy_required_fields)
    return errors


def _validate(data, truthy_fields=None, not_none_or_blank_fields=None,
              to_many_fields=None):
    errors = {}

    if truthy_fields:
        for field_name in truthy_fields:
            _validate_truthy(data.get_value(field_name), field_name, errors)

    if not_none_or_blank_fields:
        for field_name in not_none_or_blank_fields:
            _validate_not_none_or_blank(data.get_value(field_name), field_name,
                                        errors)

    if to_many_fields:
        for field_name in to_many_fields:
            _validate_truthy(data.get_value_to_many(field_name), field_name,
                             errors)
    return errors


def _validate_truthy(value, field_name, errors):
    if not value:
        errors[field_name] = REQUIRED_MESSAGE


def _validate_not_none_or_blank(value, field_name, errors):
    if value in (None, ''):
        errors[field_name] = REQUIRED_MESSAGE


class _UpdatedDataView:
    def __init__(self, instance, update_data):
        if instance is None and update_data is None:
            raise TypeError('One of instance and update_data must be provided '
                            'and not None')

        if update_data is None:
            update_data = {}

        self.instance = instance
        self.data = update_data

    def get_value(self, field_name):
        if field_name in self.data:
            return self.data[field_name]
        if self.instance:
            return getattr(self.instance, field_name)
        return None

    def get_value_to_many(self, field_name):
        if field_name in self.data:
            return self.data[field_name]
        if self.instance:
            return getattr(self.instance, field_name).all()
        return None

    def get_value_id(self, field_name):
        value = self.get_value(field_name)
        return str(value.id) if value else None
