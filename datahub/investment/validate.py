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

    data = _UpdatedDataView(instance, update_data)

    errors = {}
    truthy_required_fields = [
        'sector',
        'referral_source_advisor',
        'client_relationship_manager',
        'investor_company',
        'referral_source_activity'
    ]

    to_many_required_fields = [
        'client_contacts',
        'business_activity'
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

    for field_name in truthy_required_fields:
        _validate_truthy(data.get_value(field_name), field_name, errors)

    for field_name in to_many_required_fields:
        _validate_truthy(data.get_value_to_many(field_name), field_name,
                         errors)

    return errors


def _validate_truthy(value, field_name, errors):
    if not value:
        errors[field_name] = REQUIRED_MESSAGE


def _validate_string_or_number(value, field_name, errors):
    if value not in (None, ''):
        errors[field_name] = REQUIRED_MESSAGE


class _UpdatedDataView:
    def __init__(self, instance, data):
        self.instance = instance
        self.data = data

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
