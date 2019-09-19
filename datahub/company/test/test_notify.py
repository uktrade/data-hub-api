from unittest import mock

import pytest
from django.test.utils import override_settings

from datahub.company.constants import NOTIFY_DNB_INVESTIGATION_FEATURE_FLAG
from datahub.company.notify import (
    get_dnb_investigation_context,
    notify_new_dnb_investigation,
    Template,
)
from datahub.company.test.factories import CompanyFactory
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.notification.constants import NotifyServiceName

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'investigation_data',
    (
        None,
        {},
        {'foo': 'bar'},
        {'telephone_number': '12345678'},
        {'telephone_number': None},
    ),
)
def test_get_dnb_investigation_context(investigation_data):
    """
    Test if get_dnb_investigation_context returns a dict with sensible
    values for the required fields.
    """
    company = CompanyFactory(dnb_investigation_data=investigation_data)
    investigation_data = investigation_data or {}
    address_parts = [
        company.address_1,
        company.address_2,
        company.address_town,
        company.address_county,
        company.address_country.name,
        company.address_postcode,
    ]
    expected_address = ', '.join(
        address_part for address_part in address_parts if address_part
    )
    assert get_dnb_investigation_context(company) == {
        'business_name': company.name,
        'business_address': expected_address,
        'website': company.website or '',
        'contact_number': investigation_data.get('telephone_number') or '',
    }


def test_notify_new_dnb_investigation(monkeypatch):
    """
    Test notify_new_dnb_investigation triggers a call to the expected notification helper function.
    """
    FeatureFlagFactory(code=NOTIFY_DNB_INVESTIGATION_FEATURE_FLAG, is_active=True)
    mocked_notify_by_email = mock.Mock()
    notification_recipients = ['a@example.net', 'b@example.net']
    company = CompanyFactory(dnb_investigation_data={'telephone_number': '12345678'})
    monkeypatch.setattr(
        'datahub.notification.notify.notify_by_email', mocked_notify_by_email,
    )
    with override_settings(
        DNB_INVESTIGATION_NOTIFICATION_RECIPIENTS=notification_recipients,
    ):
        notify_new_dnb_investigation(company)
    mocked_calls = mocked_notify_by_email.call_args_list
    for email, call_args in zip(notification_recipients, mocked_calls):
        assert call_args[0] == email
        assert call_args[1] == Template.request_new_business_record.value
        assert call_args[2]['business_name'] == company.name
        expected_phone_number = company.dnb_investigation_data['telephone_number']
        assert call_args[2]['contact_number'] == expected_phone_number
        assert call_args[3] == NotifyServiceName.dnb_investigation
        mocked_notify_by_email.call_count == 2


def test_notify_new_dnb_investigation_no_feature_flag(monkeypatch):
    """
    Test notify_new_dnb_investigation triggers a call to the expected notification helper function.
    """
    mocked_notify_by_email = mock.Mock()
    notification_recipients = ['a@example.net', 'b@example.net']
    company = CompanyFactory(dnb_investigation_data={'telephone_number': '12345678'})
    monkeypatch.setattr(
        'datahub.notification.notify.notify_by_email', mocked_notify_by_email,
    )
    with override_settings(
        DNB_INVESTIGATION_NOTIFICATION_RECIPIENTS=notification_recipients,
    ):
        notify_new_dnb_investigation(company)
    mocked_notify_by_email.assert_not_called()
