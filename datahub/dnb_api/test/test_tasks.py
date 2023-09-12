from datetime import datetime, timedelta
from unittest import mock
from urllib.parse import urljoin

import pytest
from django.conf import settings
from django.forms.models import model_to_dict
from django.test.utils import override_settings
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from reversion.models import Version

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.core import serializers
from datahub.core.queues.errors import RetryError
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.dnb_api.tasks import (
    get_company_updates,
    sync_company_with_dnb,
    sync_outdated_companies_with_dnb,
    update_company_from_dnb_data,
)
from datahub.dnb_api.tasks.sync import schedule_sync_outdated_companies_with_dnb
from datahub.dnb_api.tasks.update import record_audit, schedule_get_company_updates
from datahub.dnb_api.test.utils import model_to_dict_company
from datahub.dnb_api.utils import (
    DNBServiceConnectionError,
    DNBServiceError,
    DNBServiceTimeoutError,
)
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.metadata.models import Country

pytestmark = pytest.mark.django_db


DNB_V2_SEARCH_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'v2/companies/search/')


@pytest.mark.parametrize(
    'update_descriptor',
    (
        None,
        'command:foo:bar',
    ),
)
@freeze_time('2019-01-01 11:12:13')
def test_sync_company_with_dnb_all_fields(
    requests_mock,
    dnb_response_uk,
    base_company_dict,
    update_descriptor,
):
    """
    Test the sync_company_with_dnb task when all fields should be synced.
    """
    requests_mock.post(
        DNB_V2_SEARCH_URL,
        json=dnb_response_uk,
    )
    company = CompanyFactory(duns_number='123456789')
    original_company = Company.objects.get(id=company.id)

    sync_company_with_dnb(
        company.id,
        update_descriptor=update_descriptor,
    )

    company.refresh_from_db()
    uk_country = Country.objects.get(iso_alpha2_code='GB')
    assert model_to_dict_company(company) == {
        **base_company_dict,
        'address_1': 'Unit 10, Ockham Drive',
        'address_2': '',
        'address_country': uk_country.id,
        'address_county': '',
        'address_postcode': 'UB6 0F2',
        'address_area': None,
        'address_town': 'GREENFORD',
        'archived_documents_url_path': original_company.archived_documents_url_path,
        'business_type': original_company.business_type_id,
        'company_number': '01261539',
        'created_by': original_company.created_by_id,
        'duns_number': '123456789',
        'employee_range': original_company.employee_range_id,
        'export_experience_category': original_company.export_experience_category_id,
        'global_ultimate_duns_number': '291332174',
        'id': original_company.id,
        'is_number_of_employees_estimated': True,
        'modified_by': original_company.modified_by_id,
        'name': 'FOO BICYCLE LIMITED',
        'number_of_employees': 260,
        'sector': original_company.sector_id,
        'export_segment': original_company.export_segment,
        'export_sub_segment': original_company.export_sub_segment,
        'turnover': 50651895,
        'turnover_range': original_company.turnover_range_id,
        'uk_region': original_company.uk_region_id,
        'dnb_modified_on': now(),
        'strategy': '',
        'is_out_of_business': original_company.is_out_of_business,
    }

    versions = list(Version.objects.get_for_object(company))
    assert len(versions) == 1
    version = versions[0]
    expected_update_descriptor = f'rq:sync_company_with_dnb:{company.id}'
    if update_descriptor:
        expected_update_descriptor = update_descriptor
    assert version.revision.comment == f'Updated from D&B [{expected_update_descriptor}]'
    assert version.revision.user is None


@freeze_time('2019-01-01 11:12:13')
def test_sync_company_with_dnb_partial_fields(
    requests_mock,
    dnb_response_uk,
    base_company_dict,
):
    """
    Test the sync_company_with_dnb task when only a subset of fields should be synced.
    """
    requests_mock.post(
        DNB_V2_SEARCH_URL,
        json=dnb_response_uk,
    )
    company = CompanyFactory(duns_number='123456789')
    original_company = Company.objects.get(id=company.id)
    sync_company_with_dnb(
        company.id,
        fields_to_update=['global_ultimate_duns_number'],
    )
    company.refresh_from_db()
    assert model_to_dict(company) == {
        **base_company_dict,
        'address_1': original_company.address_1,
        'address_2': original_company.address_2,
        'address_country': original_company.address_country_id,
        'address_county': original_company.address_county,
        'address_postcode': original_company.address_postcode,
        'address_area': original_company.address_area,
        'address_town': original_company.address_town,
        'archived_documents_url_path': original_company.archived_documents_url_path,
        'business_type': original_company.business_type_id,
        'created_by': original_company.created_by_id,
        'duns_number': original_company.duns_number,
        'employee_range': original_company.employee_range_id,
        'export_experience_category': original_company.export_experience_category_id,
        'global_ultimate_duns_number': '291332174',
        'id': original_company.id,
        'is_number_of_employees_estimated': original_company.is_number_of_employees_estimated,
        'is_turnover_estimated': original_company.is_turnover_estimated,
        'modified_by': original_company.modified_by_id,
        'name': original_company.name,
        'number_of_employees': original_company.number_of_employees,
        'registered_address_1': original_company.registered_address_1,
        'registered_address_2': original_company.registered_address_2,
        'registered_address_country': original_company.registered_address_country_id,
        'registered_address_county': original_company.registered_address_county,
        'registered_address_postcode': original_company.registered_address_postcode,
        'registered_address_area': original_company.registered_address_area,
        'registered_address_town': original_company.registered_address_town,
        'sector': original_company.sector_id,
        'export_segment': original_company.export_segment,
        'export_sub_segment': original_company.export_sub_segment,
        'trading_names': original_company.trading_names,
        'turnover': original_company.turnover,
        'turnover_range': original_company.turnover_range_id,
        'uk_region': original_company.uk_region_id,
        'website': original_company.website,
        'dnb_modified_on': now(),
        'strategy': '',
        'is_out_of_business': original_company.is_out_of_business,
    }


@pytest.mark.parametrize(
    'error',
    (
        DNBServiceError('An error occurred', status_code=504),
        DNBServiceError('An error occurred', status_code=503),
        DNBServiceError('An error occurred', status_code=502),
        DNBServiceError('An error occurred', status_code=500),
        DNBServiceError('An error occurred', status_code=403),
        DNBServiceError('An error occurred', status_code=400),
        DNBServiceConnectionError('An error occurred'),
        DNBServiceTimeoutError('An error occurred'),
    ),
)
def test_sync_company_with_dnb_bubbles_up_errors(monkeypatch, error):
    """
    Test the sync_company_with_dnb task retries server errors.
    """
    company = CompanyFactory(duns_number='123456789')

    # Set up a DNBServiceError with the parametrized status code
    mocked_get_company = mock.Mock()
    mocked_get_company.side_effect = error
    monkeypatch.setattr('datahub.dnb_api.tasks.sync.get_company', mocked_get_company)

    with pytest.raises(type(error)):
        sync_company_with_dnb(company.id)


class TestGetCompanyUpdates:
    @pytest.mark.parametrize(
        'error',
        (
            DNBServiceError(
                'An error occurred',
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            ),
            DNBServiceError(
                'An error occurred',
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            ),
            DNBServiceError(
                'An error occurred',
                status_code=status.HTTP_502_BAD_GATEWAY,
            ),
            DNBServiceError(
                'An error occurred',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ),
            DNBServiceError(
                'An error occurred',
                status_code=403,
            ),
            DNBServiceError(
                'An error occurred',
                status_code=400,
            ),
            DNBServiceConnectionError(
                'An error occurred',
            ),
            DNBServiceTimeoutError(
                'An error occurred',
            ),
        ),
    )
    def test_errors(self, monkeypatch, error):
        """
        Test the schedule_get_company_updates task retries server errors.
        """
        mocked_get_company_update_page = mock.Mock(side_effect=error)
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.update.get_company_update_page',
            mocked_get_company_update_page,
        )

        with pytest.raises(type(error)):
            get_company_updates()

    @pytest.mark.parametrize(
        'data',
        (
            {
                None: {
                    'next': 'http://foo.bar/companies?cursor=page2',
                    'previous': None,
                    'count': 3,
                    'results': [
                        {'foo': 1},
                        {'bar': 2},
                    ],
                },
                'http://foo.bar/companies?cursor=page2': {
                    'next': None,
                    'previous': 'http://foo.bar/companies',
                    'count': 3,
                    'results': [
                        {'baz': 3},
                    ],
                },
            },
        ),
    )
    @pytest.mark.parametrize(
        'fields_to_update',
        (
            None,
            ['foo', 'bar'],
        ),
    )
    @freeze_time('2019-01-02T2:00:00')
    def test_updates(self, monkeypatch, data, fields_to_update):
        """
        Test if the update_company task is called with the right parameters for all the records
        spread across pages.
        """
        mock_get_company_update_page = mock.Mock(
            side_effect=lambda _, next_page: data[next_page],
        )
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.update.get_company_update_page',
            mock_get_company_update_page,
        )
        job_scheduler_mock = mock.Mock(wraps=job_scheduler)
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.update.job_scheduler',
            job_scheduler_mock,
        )

        get_company_updates(
            fields_to_update=fields_to_update,
        )

        assert mock_get_company_update_page.call_count == 2
        mock_get_company_update_page.assert_any_call(
            '2019-01-01T00:00:00',
            None,
        )
        mock_get_company_update_page.assert_any_call(
            '2019-01-01T00:00:00',
            'http://foo.bar/companies?cursor=page2',
        )

        assert job_scheduler_mock.call_count == 4
        assert str(update_company_from_dnb_data) in str(job_scheduler_mock.call_args_list)
        assert str(record_audit) in str(job_scheduler_mock.call_args_list)

    @pytest.mark.parametrize(
        'lock_acquired, call_count',
        (
            (False, 0),
            (True, 1),
        ),
    )
    def test_lock(self, monkeypatch, lock_acquired, call_count):
        """
        Test that the task doesn't run if it cannot acquire
        the advisory_lock.
        """
        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.update.advisory_lock',
            mock_advisory_lock,
        )
        mock_get_company_updates = mock.Mock()
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.update._get_company_updates',
            mock_get_company_updates,
        )

        schedule_get_company_updates()

        assert mock_get_company_updates.call_count == call_count

    @pytest.mark.parametrize(
        'data',
        (
            # Test limit works correctly on the first page
            {
                None: {
                    'next': None,
                    'previous': None,
                    'count': 3,
                    'results': [
                        {'foo': 1},
                        {'bar': 2},
                        {'baz': 3},
                    ],
                },
            },
            # Test limit works correctly on the second page
            {
                None: {
                    'next': 'http://foo.bar/companies?cursor=page2',
                    'previous': None,
                    'count': 3,
                    'results': [
                        {'foo': 1},
                    ],
                },
                'http://foo.bar/companies?cursor=page2': {
                    'next': None,
                    'previous': 'http://foo.bar/companies',
                    'count': 3,
                    'results': [
                        {'bar': 2},
                        {'baz': 3},
                    ],
                },
            },
        ),
    )
    @freeze_time('2019-01-02T2:00:00')
    @override_settings(DNB_AUTOMATIC_UPDATE_LIMIT=2)
    def test_updates_max_update_limit(self, monkeypatch, data):
        """
        Test if the update_company task is called with the
        right parameters for all the records spread across
        pages.
        """
        mock_get_company_update_page = mock.Mock(
            side_effect=lambda _, next_page: data[next_page],
        )
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.update.get_company_update_page',
            mock_get_company_update_page,
        )
        job_scheduler_mock = mock.Mock(wraps=job_scheduler)
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.update.job_scheduler',
            job_scheduler_mock,
        )

        get_company_updates()

        assert job_scheduler_mock.call_count == 3
        assert str(update_company_from_dnb_data) in str(job_scheduler_mock.call_args_list)
        assert str(record_audit) in str(job_scheduler_mock.call_args_list)

    @mock.patch('datahub.dnb_api.tasks.update.send_realtime_message')
    @mock.patch('datahub.dnb_api.tasks.update.log_to_sentry')
    @freeze_time('2019-01-02T2:00:00')
    def test_updates_with_update_company_from_dnb_data(
        self,
        mocked_log_to_sentry,
        mocked_send_realtime_message,
        monkeypatch,
        dnb_company_updates_response_uk,
    ):
        """
        Test full integration for the `get_company_updates` task with the
        `update_company_from_dnb_data` task when all fields are updated.
        """
        company = CompanyFactory(duns_number='123456789')
        mock_get_company_update_page = mock.Mock(
            return_value=dnb_company_updates_response_uk,
        )
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.update.get_company_update_page',
            mock_get_company_update_page,
        )
        get_company_updates()

        company.refresh_from_db()
        dnb_company = dnb_company_updates_response_uk['results'][0]
        assert company.name == dnb_company['primary_name']
        expected_gu_number = dnb_company['global_ultimate_duns_number']
        assert company.global_ultimate_duns_number == expected_gu_number
        mocked_log_to_sentry.assert_called_with(
            'get_company_updates task completed.',
            extra={
                'success_count': 1,
                'failure_count': 0,
                'job_count': 1,
                'start_time': '2019-01-02T02:00:00+00:00',
                'end_time': '2019-01-02T02:00:00+00:00',
            },
        )
        expected_message = (
            'datahub.dnb_api.tasks.update.get_company_updates ' 'updated: 1; failed to update: 0'
        )
        mocked_send_realtime_message.assert_called_once_with(expected_message)

    @mock.patch('datahub.dnb_api.tasks.update.send_realtime_message')
    @mock.patch('datahub.dnb_api.tasks.update.log_to_sentry')
    @freeze_time('2019-01-02T2:00:00')
    def test_updates_with_update_company_from_dnb_data_partial_fields(
        self,
        mocked_log_to_sentry,
        mocked_send_realtime_message,
        monkeypatch,
        dnb_company_updates_response_uk,
    ):
        """
        Test full integration for the `get_company_updates` task with the
        `update_company_from_dnb_data` task when the fields are only partially updated.
        """
        company = CompanyFactory(duns_number='123456789')
        mock_get_company_update_page = mock.Mock(
            return_value=dnb_company_updates_response_uk,
        )
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.update.get_company_update_page',
            mock_get_company_update_page,
        )

        get_company_updates(fields_to_update=['name'])

        company.refresh_from_db()
        dnb_company = dnb_company_updates_response_uk['results'][0]
        assert company.name == dnb_company['primary_name']
        assert company.global_ultimate_duns_number == ''

        mocked_log_to_sentry.assert_called_with(
            'get_company_updates task completed.',
            extra={
                'success_count': 1,
                'failure_count': 0,
                'job_count': 1,
                'start_time': '2019-01-02T02:00:00+00:00',
                'end_time': '2019-01-02T02:00:00+00:00',
            },
        )
        expected_message = (
            'datahub.dnb_api.tasks.update.get_company_updates ' 'updated: 1; failed to update: 0'
        )
        mocked_send_realtime_message.assert_called_once_with(expected_message)

    @mock.patch('datahub.dnb_api.tasks.update.send_realtime_message')
    @mock.patch('datahub.dnb_api.tasks.update.log_to_sentry')
    @freeze_time('2019-01-02T2:00:00')
    def test_updates_with_update_company_from_dnb_data_with_failure(
        self,
        mocked_log_to_sentry,
        mocked_send_realtime_message,
        monkeypatch,
        dnb_company_updates_response_uk,
    ):
        """
        Test full integration for the `get_company_updates` task with the
        `update_company_from_dnb_data` task when all fields are updated and one company in the
        dnb-service result does not exist in Data Hub.
        """
        company = CompanyFactory(duns_number='123456789')
        missing_dnb_company = {
            **dnb_company_updates_response_uk['results'][0],
            'duns_number': '999999999',
        }
        dnb_company_updates_response_uk['results'].append(missing_dnb_company)
        mock_get_company_update_page = mock.Mock(
            return_value=dnb_company_updates_response_uk,
        )
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.update.get_company_update_page',
            mock_get_company_update_page,
        )
        get_company_updates()

        company.refresh_from_db()
        dnb_company = dnb_company_updates_response_uk['results'][0]
        assert company.name == dnb_company['primary_name']
        expected_gu_number = dnb_company['global_ultimate_duns_number']
        assert company.global_ultimate_duns_number == expected_gu_number
        mocked_log_to_sentry.assert_called_with(
            'get_company_updates task completed.',
            extra={
                'success_count': 1,
                'failure_count': 1,
                'job_count': 2,
                'start_time': '2019-01-02T02:00:00+00:00',
                'end_time': '2019-01-02T02:00:00+00:00',
            },
        )
        expected_message = (
            'datahub.dnb_api.tasks.update.get_company_updates ' 'updated: 1; failed to update: 1'
        )
        mocked_send_realtime_message.assert_called_once_with(expected_message)


@freeze_time('2019-01-01 11:12:13')
def test_update_company_from_dnb_data(dnb_response_uk, base_company_dict):
    """
    Test the update_company_from_dnb_data command when all DNB fields are updated.
    """
    company = CompanyFactory(duns_number='123456789')
    original_company = Company.objects.get(id=company.id)
    update_descriptor = 'foobar'
    update_company_from_dnb_data(
        dnb_response_uk['results'][0],
        update_descriptor=update_descriptor,
    )
    company.refresh_from_db()
    uk_country = Country.objects.get(iso_alpha2_code='GB')
    assert model_to_dict_company(company) == {
        **base_company_dict,
        'address_1': 'Unit 10, Ockham Drive',
        'address_2': '',
        'address_country': uk_country.id,
        'address_county': '',
        'address_postcode': 'UB6 0F2',
        'address_area': None,
        'address_town': 'GREENFORD',
        'archived_documents_url_path': original_company.archived_documents_url_path,
        'business_type': original_company.business_type_id,
        'company_number': '01261539',
        'created_by': original_company.created_by_id,
        'duns_number': '123456789',
        'employee_range': original_company.employee_range_id,
        'export_experience_category': original_company.export_experience_category_id,
        'global_ultimate_duns_number': '291332174',
        'id': original_company.id,
        'is_number_of_employees_estimated': True,
        'modified_by': original_company.modified_by_id,
        'name': 'FOO BICYCLE LIMITED',
        'number_of_employees': 260,
        'sector': original_company.sector_id,
        'export_segment': original_company.export_segment,
        'export_sub_segment': original_company.export_sub_segment,
        'turnover': 50651895,
        'turnover_range': original_company.turnover_range_id,
        'uk_region': original_company.uk_region_id,
        'dnb_modified_on': now(),
        'strategy': '',
        'is_out_of_business': original_company.is_out_of_business,
    }

    versions = list(Version.objects.get_for_object(company))
    assert len(versions) == 1
    version = versions[0]
    assert version.revision.comment == f'Updated from D&B [{update_descriptor}]'


@freeze_time('2019-01-01 11:12:13')
def test_update_company_from_dnb_data_partial_fields(dnb_response_uk, base_company_dict):
    """
    Test the update_company_from_dnb_data command when a subset of DNB fields are updated.
    """
    company = CompanyFactory(duns_number='123456789')
    original_company = Company.objects.get(id=company.id)

    update_company_from_dnb_data(
        dnb_response_uk['results'][0],
        fields_to_update=['global_ultimate_duns_number'],
    )
    company.refresh_from_db()
    assert model_to_dict(company) == {
        **base_company_dict,
        'address_1': original_company.address_1,
        'address_2': original_company.address_2,
        'address_country': original_company.address_country_id,
        'address_county': original_company.address_county,
        'address_postcode': original_company.address_postcode,
        'address_area': original_company.address_area,
        'address_town': original_company.address_town,
        'archived_documents_url_path': original_company.archived_documents_url_path,
        'business_type': original_company.business_type_id,
        'created_by': original_company.created_by_id,
        'duns_number': original_company.duns_number,
        'employee_range': original_company.employee_range_id,
        'export_experience_category': original_company.export_experience_category_id,
        'global_ultimate_duns_number': '291332174',
        'id': original_company.id,
        'is_number_of_employees_estimated': original_company.is_number_of_employees_estimated,
        'is_turnover_estimated': original_company.is_turnover_estimated,
        'modified_by': original_company.modified_by_id,
        'name': original_company.name,
        'number_of_employees': original_company.number_of_employees,
        'registered_address_1': original_company.registered_address_1,
        'registered_address_2': original_company.registered_address_2,
        'registered_address_country': original_company.registered_address_country_id,
        'registered_address_county': original_company.registered_address_county,
        'registered_address_area': original_company.registered_address_area,
        'registered_address_postcode': original_company.registered_address_postcode,
        'registered_address_town': original_company.registered_address_town,
        'sector': original_company.sector_id,
        'export_segment': original_company.export_segment,
        'export_sub_segment': original_company.export_sub_segment,
        'trading_names': original_company.trading_names,
        'turnover': original_company.turnover,
        'turnover_range': original_company.turnover_range_id,
        'uk_region': original_company.uk_region_id,
        'website': original_company.website,
        'dnb_modified_on': now(),
        'strategy': '',
        'is_out_of_business': original_company.is_out_of_business,
    }


@freeze_time('2019-01-01 11:12:13')
def test_update_company_from_dnb_data_does_not_exist(dnb_response_uk, caplog):
    """
    Test the update_company_from_dnb_data command when the company does not exist in Data Hub.
    """
    with pytest.raises(Company.DoesNotExist):
        update_company_from_dnb_data(dnb_response_uk['results'][0])
    assert 'Company matching duns_number was not found' in caplog.text


@freeze_time('2019-01-01 11:12:13')
def test_update_company_from_dnb_data_fails_validation(dnb_response_uk, caplog):
    """
    Test the update_company_from_dnb_data command when the company data does not pass validation
    checks.
    """
    CompanyFactory(duns_number='123456789')
    dnb_response_uk['results'][0]['primary_name'] = 'a' * 9999

    with pytest.raises(serializers.ValidationError):
        update_company_from_dnb_data(dnb_response_uk['results'][0])
    assert 'Data from D&B did not pass the Data Hub validation checks.' in caplog.text


@pytest.mark.parametrize(
    'existing_company_dnb_modified_on',
    (
        now,
        None,
    ),
)
@freeze_time('2019-01-01 11:12:13')
def test_sync_outdated_companies_with_dnb_all_fields(
    requests_mock,
    dnb_response_uk,
    base_company_dict,
    existing_company_dnb_modified_on,
    caplog,
):
    """
    Test the sync_outdated_companies_with_dnb task when all fields should be synced.
    """
    caplog.set_level('INFO')
    if callable(existing_company_dnb_modified_on):
        existing_company_dnb_modified_on = existing_company_dnb_modified_on()
    requests_mock.post(
        DNB_V2_SEARCH_URL,
        json=dnb_response_uk,
    )
    company = CompanyFactory(
        duns_number='123456789',
        dnb_modified_on=existing_company_dnb_modified_on,
    )
    original_company = Company.objects.get(id=company.id)
    schedule_sync_outdated_companies_with_dnb(
        dnb_modified_on_before=now() + timedelta(days=1),
        simulate=False,
    )
    expected_message = f'Syncing dnb-linked company "{company.id}" Succeeded'
    assert expected_message in caplog.text
    company.refresh_from_db()
    uk_country = Country.objects.get(iso_alpha2_code='GB')
    assert model_to_dict_company(company) == {
        **base_company_dict,
        'address_1': 'Unit 10, Ockham Drive',
        'address_2': '',
        'address_country': uk_country.id,
        'address_county': '',
        'address_postcode': 'UB6 0F2',
        'address_area': None,
        'address_town': 'GREENFORD',
        'archived_documents_url_path': original_company.archived_documents_url_path,
        'business_type': original_company.business_type_id,
        'company_number': '01261539',
        'created_by': original_company.created_by_id,
        'duns_number': '123456789',
        'employee_range': original_company.employee_range_id,
        'export_experience_category': original_company.export_experience_category_id,
        'global_ultimate_duns_number': '291332174',
        'id': original_company.id,
        'is_number_of_employees_estimated': True,
        'modified_by': original_company.modified_by_id,
        'name': 'FOO BICYCLE LIMITED',
        'number_of_employees': 260,
        'sector': original_company.sector_id,
        'export_segment': original_company.export_segment,
        'export_sub_segment': original_company.export_sub_segment,
        'turnover': 50651895,
        'turnover_range': original_company.turnover_range_id,
        'uk_region': original_company.uk_region_id,
        'dnb_modified_on': now(),
        'strategy': '',
        'is_out_of_business': original_company.is_out_of_business,
    }


@pytest.mark.parametrize(
    'existing_company_dnb_modified_on',
    (
        now,
        None,
    ),
)
@freeze_time('2019-01-01 11:12:13')
def test_sync_outdated_companies_with_dnb_partial_fields(
    requests_mock,
    dnb_response_uk,
    base_company_dict,
    existing_company_dnb_modified_on,
    caplog,
):
    """
    Test the sync_outdated_companies_with_dnb task when only a subset of fields should be synced.
    """
    caplog.set_level('INFO')
    if callable(existing_company_dnb_modified_on):
        existing_company_dnb_modified_on = existing_company_dnb_modified_on()
    requests_mock.post(
        DNB_V2_SEARCH_URL,
        json=dnb_response_uk,
    )
    company = CompanyFactory(
        duns_number='123456789',
        dnb_modified_on=existing_company_dnb_modified_on,
    )
    original_company = Company.objects.get(id=company.id)
    schedule_sync_outdated_companies_with_dnb(
        fields_to_update=['global_ultimate_duns_number'],
        dnb_modified_on_before=now() + timedelta(days=1),
        simulate=False,
    )
    company.refresh_from_db()
    assert model_to_dict(company) == {
        **base_company_dict,
        'address_1': original_company.address_1,
        'address_2': original_company.address_2,
        'address_country': original_company.address_country_id,
        'address_county': original_company.address_county,
        'address_area': original_company.address_area,
        'address_postcode': original_company.address_postcode,
        'address_town': original_company.address_town,
        'archived_documents_url_path': original_company.archived_documents_url_path,
        'business_type': original_company.business_type_id,
        'company_number': original_company.company_number,
        'created_by': original_company.created_by_id,
        'duns_number': original_company.duns_number,
        'employee_range': original_company.employee_range_id,
        'export_experience_category': original_company.export_experience_category_id,
        'global_ultimate_duns_number': '291332174',
        'id': original_company.id,
        'is_number_of_employees_estimated': original_company.is_number_of_employees_estimated,
        'is_turnover_estimated': original_company.is_turnover_estimated,
        'modified_by': original_company.modified_by_id,
        'name': original_company.name,
        'number_of_employees': original_company.number_of_employees,
        'registered_address_1': original_company.registered_address_1,
        'registered_address_2': original_company.registered_address_2,
        'registered_address_country': original_company.registered_address_country_id,
        'registered_address_county': original_company.registered_address_county,
        'registered_address_area': original_company.registered_address_area,
        'registered_address_postcode': original_company.registered_address_postcode,
        'registered_address_town': original_company.registered_address_town,
        'sector': original_company.sector_id,
        'export_segment': original_company.export_segment,
        'export_sub_segment': original_company.export_sub_segment,
        'trading_names': original_company.trading_names,
        'turnover': original_company.turnover,
        'turnover_range': original_company.turnover_range_id,
        'uk_region': original_company.uk_region_id,
        'website': original_company.website,
        'dnb_modified_on': now(),
        'strategy': '',
        'is_out_of_business': original_company.is_out_of_business,
    }
    expected_message = f'Syncing dnb-linked company "{company.id}" Succeeded'
    assert expected_message in caplog.text


@freeze_time('2019-01-01 11:12:13')
def test_sync_outdated_companies_limit_least_recently_synced_is_updated(
    requests_mock,
    dnb_response_uk,
):
    """
    Test that running sync_outdated_companies_with_dnb with a limit will update
    the least recently synced company.
    """
    requests_mock.post(
        DNB_V2_SEARCH_URL,
        json=dnb_response_uk,
    )
    company_1 = CompanyFactory(
        duns_number='123456788',
        dnb_modified_on=now() - timedelta(days=1),
    )
    original_company_1 = Company.objects.get(id=company_1.id)
    company_2 = CompanyFactory(
        duns_number='123456789',
        dnb_modified_on=now() - timedelta(days=2),
    )

    schedule_sync_outdated_companies_with_dnb(
        fields_to_update=['global_ultimate_duns_number'],
        dnb_modified_on_before=now() + timedelta(days=1),
        simulate=False,
        limit=1,
    )

    company_1.refresh_from_db()
    company_2.refresh_from_db()
    # We expect company_1 to be unmodified
    assert company_1.dnb_modified_on == original_company_1.dnb_modified_on
    # We expect company_2 to be modified, as it was least recently synced with D&B
    assert company_2.dnb_modified_on == now()


@freeze_time('2019-01-01 11:12:13')
def test_sync_outdated_companies_limit_most_recently_interacted_updated(
    requests_mock,
    dnb_response_uk,
):
    """
    Test that running sync_outdated_companies_with_dnb with a limit will update
    the most recently interacted company.
    """
    requests_mock.post(
        DNB_V2_SEARCH_URL,
        json=dnb_response_uk,
    )

    company_most_recent_interaction = CompanyFactory(
        duns_number='123456789',
        dnb_modified_on=now() - timedelta(days=1),
    )
    CompanyInteractionFactory(company=company_most_recent_interaction, date=now())

    company_least_recent_interaction = CompanyFactory(
        duns_number='123456788',
        dnb_modified_on=now() - timedelta(days=1),
    )
    CompanyInteractionFactory(
        company=company_least_recent_interaction,
        date=now() - timedelta(days=1),
    )

    sync_outdated_companies_with_dnb(
        fields_to_update=['global_ultimate_duns_number'],
        dnb_modified_on_before=now() + timedelta(days=1),
        simulate=False,
        limit=1,
        max_requests=10,
    )

    company_least_recent_interaction.refresh_from_db()
    company_most_recent_interaction.refresh_from_db()
    # We expect the least recently interacted company to be unmodified
    assert company_least_recent_interaction.dnb_modified_on == now() - timedelta(days=1)
    # We expect most recently interacted company to be modified
    assert company_most_recent_interaction.dnb_modified_on == now()


@freeze_time('2019-01-01 11:12:13')
def test_sync_outdated_companies_nothing_to_update(
    requests_mock,
    dnb_response_uk,
):
    """
    Add two companies (one with dnb_modified_on>dnb_modified_on_before) and
    assert that only the outdated one is synced.
    """
    company = CompanyFactory(
        duns_number='123456789',
        dnb_modified_on=now() - timedelta(days=5),
    )
    original_company = Company.objects.get(id=company.id)

    sync_outdated_companies_with_dnb(
        fields_to_update=['global_ultimate_duns_number'],
        dnb_modified_on_before=now() - timedelta(days=1),
        simulate=False,
        limit=1,
    )

    company.refresh_from_db()
    # We expect the company to be unmodified
    assert company.dnb_modified_on == original_company.dnb_modified_on


@freeze_time('2019-01-01 11:12:13')
def test_sync_outdated_companies_simulation(caplog):
    """
    Test that using simulation mode does not modify companies and logs correctly.
    """
    caplog.set_level('INFO')
    company = CompanyFactory(
        duns_number='123456789',
        dnb_modified_on=now() - timedelta(days=5),
    )
    original_company = Company.objects.get(id=company.id)

    sync_outdated_companies_with_dnb(
        fields_to_update=['global_ultimate_duns_number'],
        dnb_modified_on_before=now() - timedelta(days=1),
    )

    company.refresh_from_db()
    # We expect the company to be unmodified
    assert company.dnb_modified_on == original_company.dnb_modified_on
    expected_message = f'[SIMULATION] Syncing dnb-linked company "{company.id}" Succeeded'
    assert expected_message in caplog.text


@freeze_time('2019-01-01 11:12:13')
def test_sync_outdated_companies_sync_task_failure_logs_error(caplog, monkeypatch):
    """
    Test that when the sync_company_with_dnb sub-task fails, an error log is
    generated.
    """
    caplog.set_level('WARNING')
    company = CompanyFactory(
        duns_number='123456789',
        dnb_modified_on=now() - timedelta(days=5),
    )
    mocked_sync_company_with_dnb = mock.Mock(side_effect=Exception())
    monkeypatch.setattr(
        'datahub.dnb_api.tasks.sync_company_with_dnb',
        mocked_sync_company_with_dnb,
    )

    sync_outdated_companies_with_dnb(
        fields_to_update=['global_ultimate_duns_number'],
        dnb_modified_on_before=now() - timedelta(days=1),
        simulate=False,
    )

    expected_message = f'Syncing dnb-linked company "{company.id}" Failed'
    assert expected_message in caplog.text


def test_record_audit_succeeds_when_ttl_expires(monkeypatch):
    send_realtime_message_mock = mock.Mock()
    monkeypatch.setattr(
        'datahub.dnb_api.tasks.update.send_realtime_message',
        send_realtime_message_mock,
    )
    now = datetime.utcnow()
    record_audit(
        [
            '34e8ef6e-4efb-11ed-bdc3-0242ac120002',
            '34e8f342-4efb-11ed-bdc3-0242ac120002',
            '34e8f59a-4efb-11ed-bdc3-0242ac120002',
        ],
        now,
    )
    send_realtime_message_mock.assert_called_with(
        f'datahub.dnb_api.tasks.update.get_company_updates updated: {3}; '
        f'failed to update: {0}',
    )


@mock.patch('datahub.dnb_api.tasks.update.DataHubScheduler.job')
def test_should_throw_retry_error_if_busy(scheduler_job):
    scheduler_job.return_value = mock.Mock(
        id='34e8f59a-4efb-11ed-bdc3-0242ac120002',
        is_finished=False,
        is_failed=False,
    )

    now = datetime.utcnow()

    with pytest.raises(RetryError):
        record_audit(
            [
                '34e8f59a-4efb-11ed-bdc3-0242ac120002',
            ],
            now,
        )
