from datetime import timedelta
from io import BytesIO
from unittest import mock

import pytest
from django.core.management import call_command
from freezegun import freeze_time

from datahub.company.test.factories import CompanyFactory
from datahub.dbmaintenance.management.commands.update_companies_dnb_data import (
    API_CALLS_PER_SECOND,
    Command,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_sleep(monkeypatch):
    """
    Mock time.sleep().
    """
    mocked_sleep = mock.Mock()
    monkeypatch.setattr(
        'datahub.dbmaintenance.management.commands.update_companies_dnb_data.time.sleep',
        mocked_sleep,
    )
    return mocked_sleep


@pytest.fixture
def mock_sync_company_with_dnb(monkeypatch):
    """
    Mock sync_company_with_dnb.apply().
    """
    mocked_sync_company_with_dnb = mock.Mock()
    monkeypatch.setattr(
        'datahub.dbmaintenance.management.commands.update_companies_dnb_data.'
        'sync_company_with_dnb.apply',
        mocked_sync_company_with_dnb,
    )
    return mocked_sync_company_with_dnb


@freeze_time('2019-11-12 10:00:00')
@pytest.mark.parametrize(
    'fields',
    (
        None,
        ['global_ultimate_duns_number', 'name'],
    ),
)
def test_run(s3_stubber, caplog, mock_sleep, mock_sync_company_with_dnb, fields):
    """
    Test that the command updates the specified records (ignoring ones with errors).
    """
    caplog.set_level('WARNING')

    companies = [
        CompanyFactory(duns_number='123456789'),
        CompanyFactory(duns_number='223456789'),
        CompanyFactory(duns_number='323456789'),
        CompanyFactory(duns_number='423456789'),
        CompanyFactory(),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id
00000000-0000-0000-0000-000000000000
{companies[0].id}
{companies[1].id}
{companies[2].id}
{companies[3].id}
{companies[4].id}
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content, encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    with freeze_time('2019-11-12 10:00:00') as frozen_time:
        mock_sleep.side_effect = lambda seconds: frozen_time.tick(timedelta(seconds=seconds))
        call_command('update_companies_dnb_data', bucket, object_key, fields=fields)

        assert len(caplog.records) == 4
        assert 'Company does not exist.' in caplog.text
        assert 'Company does not have a duns_number.' in caplog.text

        assert mock_sleep.call_count == 4

        assert mock_sync_company_with_dnb.call_count == 4
        for company in companies:
            if company.duns_number:
                mock_sync_company_with_dnb.assert_any_call(args=(company.id, fields))


def test_simulate(s3_stubber, caplog, mock_sleep, mock_sync_company_with_dnb):
    """
    Test that the command simulates updates if --simulate is passed in.
    """
    caplog.set_level('WARNING')

    companies = [
        CompanyFactory(duns_number='123456789'),
        CompanyFactory(duns_number='223456789'),
        CompanyFactory(duns_number='323456789'),
        CompanyFactory(duns_number='423456789'),
        CompanyFactory(),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id
00000000-0000-0000-0000-000000000000
{companies[0].id}
{companies[1].id}
{companies[2].id}
{companies[3].id}
{companies[4].id}
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content, encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    with freeze_time('2019-11-12 10:00:00'):
        call_command('update_companies_dnb_data', bucket, object_key, simulate=True)

        assert len(caplog.records) == 4
        assert 'Company does not exist.' in caplog.text
        assert 'Company does not have a duns_number.' in caplog.text

        assert mock_sync_company_with_dnb.call_count == 0


def test_limit_call_rate(mock_sleep):
    """
    Test that the _limit_call_rate() method will enforce the API_CALLS_PER_SECOND
    limit.
    """
    api_call_wait = 1 / API_CALLS_PER_SECOND
    time_at_freeze = 1573552800.0
    with freeze_time('2019-11-12 10:00:00') as frozen_time:
        mock_sleep.side_effect = lambda seconds: frozen_time.tick(timedelta(seconds=seconds))
        command = Command()

        # Call the _limit_call_rate() method and ensure that sleep is called with
        # the maximum wait time
        command._limit_call_rate()
        mock_sleep.assert_called_with(api_call_wait)
        assert command.last_called_api_time == time_at_freeze + API_CALLS_PER_SECOND

        # Simulate some execution time outside of _limit_call_rate which takes
        # (maximum wait time / 2) and ensure that sleep is called to maintain
        # the API_CALLS_PER_SECOND limit
        gap_seconds = api_call_wait / 2
        gap_ms = gap_seconds * 1000
        frozen_time.tick(timedelta(milliseconds=gap_ms))
        command._limit_call_rate()
        mock_sleep.assert_called_with(api_call_wait - gap_seconds)
