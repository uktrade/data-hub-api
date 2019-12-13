from io import BytesIO
from unittest import mock

import pytest
from django.core.management import call_command
from freezegun import freeze_time

from datahub.company.test.factories import CompanyFactory
from datahub.dbmaintenance.management.commands.update_company_dnb_data import (
    API_CALL_INTERVAL,
    Command,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_time(monkeypatch):
    """
    Mock time.sleep() and time.perf_counter().
    """
    # Freeze perf_counter's perception of time at a value of 1.0
    mock_perf_counter = mock.Mock(return_value=1.0)
    monkeypatch.setattr(
        'datahub.dbmaintenance.management.commands.update_company_dnb_data.time.perf_counter',
        mock_perf_counter,
    )

    # Introduce a mock for time.sleep which can tick our frozen time
    mock_sleep = mock.Mock()

    def sleep_side_effect(seconds):
        mock_perf_counter.return_value += seconds

    mock_sleep.side_effect = sleep_side_effect
    monkeypatch.setattr(
        'datahub.dbmaintenance.management.commands.update_company_dnb_data.time.sleep',
        mock_sleep,
    )

    return {
        'mock_sleep': mock_sleep,
        'mock_perf_counter': mock_perf_counter,
    }


@pytest.fixture
def mock_sync_company_with_dnb(monkeypatch):
    """
    Mock sync_company_with_dnb.apply().
    """
    mocked_sync_company_with_dnb = mock.Mock()
    monkeypatch.setattr(
        'datahub.dbmaintenance.management.commands.update_company_dnb_data.'
        'sync_company_with_dnb.apply',
        mocked_sync_company_with_dnb,
    )
    return mocked_sync_company_with_dnb


@pytest.mark.parametrize(
    'fields',
    (
        None,
        ['global_ultimate_duns_number', 'name'],
    ),
)
@freeze_time('2019-01-01 11:12:13')
def test_run(s3_stubber, caplog, mock_time, mock_sync_company_with_dnb, fields):
    """
    Test that the command updates the specified records (ignoring ones with errors).
    """
    mock_sleep = mock_time['mock_sleep']
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

    call_command('update_company_dnb_data', bucket, object_key, fields=fields)

    assert len(caplog.records) == 2

    assert mock_sleep.call_count == 4

    assert mock_sync_company_with_dnb.call_count == 4
    for company in companies:
        if company.duns_number:
            mock_sync_company_with_dnb.assert_any_call(
                args=(
                    company.id,
                    fields,
                    'command:update_company_dnb_data:2019-01-01T11:12:13+00:00',
                ),
            )


def test_simulate(s3_stubber, caplog, mock_time, mock_sync_company_with_dnb):
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

    call_command('update_company_dnb_data', bucket, object_key, simulate=True)

    assert len(caplog.records) == 2

    assert not mock_sync_company_with_dnb.called


def test_limit_call_rate(mock_time):
    """
    Test that the _limit_call_rate() method will enforce the API_CALLS_PER_SECOND
    limit.
    """
    mock_sleep = mock_time['mock_sleep']
    mock_perf_counter = mock_time['mock_perf_counter']
    time_at_freeze = mock_perf_counter.return_value
    command = Command()

    # Call the _limit_call_rate() method and ensure that sleep is called with
    # the maximum wait time
    command._limit_call_rate()
    assert mock_sleep.call_args == mock.call(API_CALL_INTERVAL)
    assert command.last_called_api_time == time_at_freeze + API_CALL_INTERVAL

    # Simulate some execution time outside of _limit_call_rate which takes
    # (maximum wait time / 2) and ensure that sleep is called to maintain
    # the API_CALLS_PER_SECOND limit
    gap_seconds = API_CALL_INTERVAL / 2

    # Progress our mocked perf_counter's perception of time
    mock_perf_counter.return_value += gap_seconds

    command._limit_call_rate()
    expected_sleep_time = API_CALL_INTERVAL - gap_seconds
    assert mock_sleep.call_args == mock.call(expected_sleep_time)

    # Simulate some execution time outside of _limit_call_rate which takes
    # (maximum wait time * 2) and ensure that _limit_call_rate does not
    # introduce an extra wait
    gap_seconds = API_CALL_INTERVAL * 2
    mock_sleep.reset_mock()

    # Progress our mocked perf_counter's perception of time
    mock_perf_counter.return_value += gap_seconds

    command._limit_call_rate()
    assert not mock_sleep.called
