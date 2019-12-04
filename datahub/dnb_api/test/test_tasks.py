from unittest import mock
from urllib.parse import urljoin

import pytest
from celery.exceptions import Retry
from django.conf import settings
from django.forms.models import model_to_dict
from django.test.utils import override_settings
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from reversion.models import Version

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.dnb_api.tasks import (
    get_company_updates,
    sync_company_with_dnb,
    update_company_from_dnb_data,
)
from datahub.dnb_api.utils import (
    DNBServiceConnectionError,
    DNBServiceError,
    DNBServiceTimeoutError,
)
from datahub.metadata.models import Country

pytestmark = pytest.mark.django_db


DNB_SEARCH_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'companies/search/')


@freeze_time('2019-01-01 11:12:13')
def test_sync_company_with_dnb_all_fields(
    dnb_company_search_feature_flag,
    requests_mock,
    dnb_response_uk,
):
    """
    Test the sync_company_with_dnb task when all fields should be synced.
    """
    requests_mock.post(
        DNB_SEARCH_URL,
        json=dnb_response_uk,
    )
    company = CompanyFactory(duns_number='123456789')
    original_company = Company.objects.get(id=company.id)
    task_result = sync_company_with_dnb.apply_async(args=[company.id])
    assert task_result.successful()
    company.refresh_from_db()
    uk_country = Country.objects.get(iso_alpha2_code='GB')
    assert model_to_dict(company) == {
        'address_1': 'Unit 10, Ockham Drive',
        'address_2': '',
        'address_country': uk_country.id,
        'address_county': '',
        'address_postcode': 'UB6 0F2',
        'address_town': 'GREENFORD',
        'archived': False,
        'archived_by': None,
        'archived_documents_url_path': original_company.archived_documents_url_path,
        'archived_on': None,
        'archived_reason': None,
        'business_type': original_company.business_type_id,
        'company_number': '01261539',
        'created_by': original_company.created_by_id,
        'description': None,
        'dnb_investigation_data': None,
        'duns_number': '123456789',
        'employee_range': original_company.employee_range_id,
        'export_experience_category': original_company.export_experience_category_id,
        'export_potential': None,
        'export_to_countries': [],
        'future_interest_countries': [],
        'global_headquarters': None,
        'global_ultimate_duns_number': '291332174',
        'great_profile_status': None,
        'headquarter_type': None,
        'id': original_company.id,
        'is_number_of_employees_estimated': True,
        'is_turnover_estimated': None,
        'modified_by': original_company.modified_by_id,
        'name': 'FOO BICYCLE LIMITED',
        'number_of_employees': 260,
        'one_list_account_owner': None,
        'one_list_tier': None,
        'pending_dnb_investigation': False,
        'reference_code': '',
        'registered_address_1': 'C/O LONE VARY',
        'registered_address_2': '',
        'registered_address_country': uk_country.id,
        'registered_address_county': '',
        'registered_address_postcode': 'UB6 0F2',
        'registered_address_town': 'GREENFORD',
        'sector': original_company.sector_id,
        'trading_names': [],
        'transfer_reason': '',
        'transferred_by': None,
        'transferred_on': None,
        'transferred_to': None,
        'turnover': 50651895,
        'turnover_range': original_company.turnover_range_id,
        'uk_region': original_company.uk_region_id,
        'vat_number': '',
        'website': 'http://foo.com',
        'dnb_modified_on': now(),
    }

    versions = list(Version.objects.get_for_object(company))
    assert len(versions) == 1
    version = versions[0]
    assert version.revision.comment == 'Updated from D&B [celery:sync_company_with_dnb]'
    assert version.revision.user is None


@freeze_time('2019-01-01 11:12:13')
def test_sync_company_with_dnb_partial_fields(
    dnb_company_search_feature_flag,
    requests_mock,
    dnb_response_uk,
):
    """
    Test the sync_company_with_dnb task when only a subset of fields should be synced.
    """
    requests_mock.post(
        DNB_SEARCH_URL,
        json=dnb_response_uk,
    )
    company = CompanyFactory(duns_number='123456789')
    original_company = Company.objects.get(id=company.id)
    task_result = sync_company_with_dnb.apply_async(
        args=[company.id],
        kwargs={'fields_to_update': ['global_ultimate_duns_number']},
    )
    assert task_result.successful()
    company.refresh_from_db()
    assert model_to_dict(company) == {
        'address_1': original_company.address_1,
        'address_2': original_company.address_2,
        'address_country': original_company.address_country_id,
        'address_county': original_company.address_county,
        'address_postcode': original_company.address_postcode,
        'address_town': original_company.address_town,
        'archived': original_company.archived,
        'archived_by': original_company.archived_by,
        'archived_documents_url_path': original_company.archived_documents_url_path,
        'archived_on': original_company.archived_on,
        'archived_reason': original_company.archived_reason,
        'business_type': original_company.business_type_id,
        'company_number': original_company.company_number,
        'created_by': original_company.created_by_id,
        'description': original_company.description,
        'dnb_investigation_data': original_company.dnb_investigation_data,
        'duns_number': original_company.duns_number,
        'employee_range': original_company.employee_range_id,
        'export_experience_category': original_company.export_experience_category_id,
        'export_potential': original_company.export_potential,
        'export_to_countries': [],
        'future_interest_countries': [],
        'global_headquarters': original_company.global_headquarters,
        'global_ultimate_duns_number': '291332174',
        'great_profile_status': original_company.great_profile_status,
        'headquarter_type': original_company.headquarter_type,
        'id': original_company.id,
        'is_number_of_employees_estimated': original_company.is_number_of_employees_estimated,
        'is_turnover_estimated': original_company.is_turnover_estimated,
        'modified_by': original_company.modified_by_id,
        'name': original_company.name,
        'number_of_employees': original_company.number_of_employees,
        'one_list_account_owner': original_company.one_list_account_owner,
        'one_list_tier': original_company.one_list_tier,
        'pending_dnb_investigation': original_company.pending_dnb_investigation,
        'reference_code': original_company.reference_code,
        'registered_address_1': original_company.registered_address_1,
        'registered_address_2': original_company.registered_address_2,
        'registered_address_country': original_company.registered_address_country_id,
        'registered_address_county': original_company.registered_address_county,
        'registered_address_postcode': original_company.registered_address_postcode,
        'registered_address_town': original_company.registered_address_town,
        'sector': original_company.sector_id,
        'trading_names': original_company.trading_names,
        'transfer_reason': original_company.transfer_reason,
        'transferred_by': None,
        'transferred_on': None,
        'transferred_to': None,
        'turnover': original_company.turnover,
        'turnover_range': original_company.turnover_range_id,
        'uk_region': original_company.uk_region_id,
        'vat_number': original_company.vat_number,
        'website': original_company.website,
        'dnb_modified_on': now(),
    }


@pytest.mark.parametrize(
    'error,expect_retry',
    (
        (DNBServiceError('An error occurred', status_code=504), True),
        (DNBServiceError('An error occurred', status_code=503), True),
        (DNBServiceError('An error occurred', status_code=502), True),
        (DNBServiceError('An error occurred', status_code=500), True),
        (DNBServiceError('An error occurred', status_code=403), False),
        (DNBServiceError('An error occurred', status_code=400), False),
        (DNBServiceConnectionError('An error occurred'), True),
        (DNBServiceTimeoutError('An error occurred'), True),
    ),
)
def test_sync_company_with_dnb_retries_errors(monkeypatch, error, expect_retry):
    """
    Test the sync_company_with_dnb task retries server errors.
    """
    company = CompanyFactory(duns_number='123456789')

    # Set up a DNBServiceError with the parametrized status code
    mocked_get_company = mock.Mock()
    mocked_get_company.side_effect = error
    monkeypatch.setattr('datahub.dnb_api.tasks.get_company', mocked_get_company)

    # Mock the task's retry method
    retry_mock = mock.Mock(side_effect=Retry(exc=error))
    monkeypatch.setattr('datahub.dnb_api.tasks.sync_company_with_dnb.retry', retry_mock)

    if expect_retry:
        expected_exception_class = Retry
    else:
        expected_exception_class = DNBServiceError

    with pytest.raises(expected_exception_class):
        sync_company_with_dnb(company.id)


class TestGetCompanyUpdates:
    """
    Tests for the get_company_updates task and the associated _get_company_updates function.
    """

    @pytest.mark.parametrize(
        'error, expect_retry',
        (
            (
                DNBServiceError(
                    'An error occurred',
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                ),
                True,
            ),
            (
                DNBServiceError(
                    'An error occurred',
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                ),
                True,
            ),
            (
                DNBServiceError(
                    'An error occurred',
                    status_code=status.HTTP_502_BAD_GATEWAY,
                ),
                True,
            ),
            (
                DNBServiceError(
                    'An error occurred',
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                ),
                True,
            ),
            (
                DNBServiceError(
                    'An error occurred',
                    status_code=403,
                ),
                False,
            ),
            (
                DNBServiceError(
                    'An error occurred',
                    status_code=400,
                ),
                False,
            ),
            (
                DNBServiceConnectionError(
                    'An error occurred',
                ),
                True,
            ),
            (
                DNBServiceTimeoutError(
                    'An error occurred',
                ),
                True,
            ),
        ),
    )
    def test_errors(self, monkeypatch, error, expect_retry, dnb_company_updates_feature_flag):
        """
        Test the get_company_updates task retries server errors.
        """
        mocked_get_company_update_page = mock.Mock(side_effect=error)
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.get_company_update_page',
            mocked_get_company_update_page,
        )

        mock_retry = mock.Mock(side_effect=Retry(exc=error))
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.get_company_updates.retry',
            mock_retry,
        )

        expected_exception_class = Retry if expect_retry else DNBServiceError
        with pytest.raises(expected_exception_class):
            get_company_updates()

    @pytest.mark.parametrize(
        'data',
        (
            {
                None: {
                    'next': 'page2',
                    'results': [
                        {'foo': 1},
                        {'bar': 2},
                    ],
                },
                'page2': {
                    'next': None,
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
    def test_updates(self, monkeypatch, dnb_company_updates_feature_flag, data, fields_to_update):
        """
        Test if the update_company task is called with the
        right parameters for all the records spread across
        pages.
        """
        mock_get_company_update_page = mock.Mock(
            side_effect=lambda _, cursor: data[cursor],
        )
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.get_company_update_page',
            mock_get_company_update_page,
        )
        mock_update_company = mock.Mock()
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.update_company_from_dnb_data',
            mock_update_company,
        )
        get_company_updates(fields_to_update=fields_to_update)

        assert mock_get_company_update_page.call_count == 2
        mock_get_company_update_page.assert_any_call(
            '2019-01-01T00:00:00',
            None,
        )
        mock_get_company_update_page.assert_any_call(
            '2019-01-01T00:00:00',
            'page2',
        )

        assert mock_update_company.apply_async.call_count == 3
        mock_update_company.apply_async.assert_any_call(
            args=({'foo': 1},),
            kwargs={'fields_to_update': fields_to_update},
        )
        mock_update_company.apply_async.assert_any_call(
            args=({'bar': 2},),
            kwargs={'fields_to_update': fields_to_update},
        )
        mock_update_company.apply_async.assert_any_call(
            args=({'baz': 3},),
            kwargs={'fields_to_update': fields_to_update},
        )

    @pytest.mark.parametrize(
        'lock_acquired, call_count',
        (
            (False, 0),
            (True, 1),
        ),
    )
    def test_lock(self, monkeypatch, dnb_company_updates_feature_flag, lock_acquired, call_count):
        """
        Test that the task doesn't run if it cannot acquire
        the advisory_lock.
        """
        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.advisory_lock',
            mock_advisory_lock,
        )
        mock_get_company_updates = mock.Mock()
        monkeypatch.setattr(
            'datahub.dnb_api.tasks._get_company_updates',
            mock_get_company_updates,
        )

        get_company_updates()

        assert mock_get_company_updates.call_count == call_count

    @pytest.mark.parametrize(
        'data',
        (
            # Test limit works correctly on the first page
            {
                None: {
                    'next': None,
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
                    'next': 'page2',
                    'results': [
                        {'foo': 1},
                    ],
                },
                'page2': {
                    'next': None,
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
            side_effect=lambda _, cursor: data[cursor],
        )
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.get_company_update_page',
            mock_get_company_update_page,
        )
        mock_update_company = mock.Mock()
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.update_company_from_dnb_data',
            mock_update_company,
        )
        get_company_updates()

        assert mock_update_company.apply_async.call_count == 2
        mock_update_company.apply_async.assert_any_call(
            args=({'foo': 1},),
            kwargs={'fields_to_update': None},
        )
        mock_update_company.apply_async.assert_any_call(
            args=({'bar': 2},),
            kwargs={'fields_to_update': None},
        )

    @freeze_time('2019-01-02T2:00:00')
    def test_updates_with_update_company_from_dnb_data(
        self,
        monkeypatch,
        dnb_company_updates_feature_flag,
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
            'datahub.dnb_api.tasks.get_company_update_page',
            mock_get_company_update_page,
        )
        get_company_updates()

        company.refresh_from_db()
        dnb_company = dnb_company_updates_response_uk['results'][0]
        assert company.name == dnb_company['primary_name']
        expected_gu_number = dnb_company['global_ultimate_duns_number']
        assert company.global_ultimate_duns_number == expected_gu_number

    @freeze_time('2019-01-02T2:00:00')
    def test_updates_with_update_company_from_dnb_data_partial_fields(
        self,
        monkeypatch,
        dnb_company_updates_feature_flag,
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
            'datahub.dnb_api.tasks.get_company_update_page',
            mock_get_company_update_page,
        )
        get_company_updates(fields_to_update=['name'])

        company.refresh_from_db()
        dnb_company = dnb_company_updates_response_uk['results'][0]
        assert company.name == dnb_company['primary_name']
        assert company.global_ultimate_duns_number == ''

    def test_feature_flag_inactive_no_updates(
        self,
        monkeypatch,
    ):
        """
        Test that when the DNB company updates feature flag is inactive, the task does not proceed.
        """
        mocked_get_company_update_page = mock.Mock()
        monkeypatch.setattr(
            'datahub.dnb_api.tasks.get_company_update_page',
            mocked_get_company_update_page,
        )
        get_company_updates()
        assert mocked_get_company_update_page.call_count == 0


@freeze_time('2019-01-01 11:12:13')
def test_update_company_from_dnb_data(dnb_response_uk):
    """
    Test the update_company_from_dnb_data command when all DNB fields are updated.
    """
    company = CompanyFactory(duns_number='123456789')
    original_company = Company.objects.get(id=company.id)
    task_result = update_company_from_dnb_data.apply_async(args=[dnb_response_uk['results'][0]])
    assert task_result.successful()
    company.refresh_from_db()
    uk_country = Country.objects.get(iso_alpha2_code='GB')
    assert model_to_dict(company) == {
        'address_1': 'Unit 10, Ockham Drive',
        'address_2': '',
        'address_country': uk_country.id,
        'address_county': '',
        'address_postcode': 'UB6 0F2',
        'address_town': 'GREENFORD',
        'archived': False,
        'archived_by': None,
        'archived_documents_url_path': original_company.archived_documents_url_path,
        'archived_on': None,
        'archived_reason': None,
        'business_type': original_company.business_type_id,
        'company_number': '01261539',
        'created_by': original_company.created_by_id,
        'description': None,
        'dnb_investigation_data': None,
        'duns_number': '123456789',
        'employee_range': original_company.employee_range_id,
        'export_experience_category': original_company.export_experience_category_id,
        'export_potential': None,
        'export_to_countries': [],
        'future_interest_countries': [],
        'global_headquarters': None,
        'global_ultimate_duns_number': '291332174',
        'great_profile_status': None,
        'headquarter_type': None,
        'id': original_company.id,
        'is_number_of_employees_estimated': True,
        'is_turnover_estimated': None,
        'modified_by': original_company.modified_by_id,
        'name': 'FOO BICYCLE LIMITED',
        'number_of_employees': 260,
        'one_list_account_owner': None,
        'one_list_tier': None,
        'pending_dnb_investigation': False,
        'reference_code': '',
        'registered_address_1': 'C/O LONE VARY',
        'registered_address_2': '',
        'registered_address_country': uk_country.id,
        'registered_address_county': '',
        'registered_address_postcode': 'UB6 0F2',
        'registered_address_town': 'GREENFORD',
        'sector': original_company.sector_id,
        'trading_names': [],
        'transfer_reason': '',
        'transferred_by': None,
        'transferred_on': None,
        'transferred_to': None,
        'turnover': 50651895,
        'turnover_range': original_company.turnover_range_id,
        'uk_region': original_company.uk_region_id,
        'vat_number': '',
        'website': 'http://foo.com',
        'dnb_modified_on': now(),
    }


@freeze_time('2019-01-01 11:12:13')
def test_update_company_from_dnb_data_partial_fields(dnb_response_uk):
    """
    Test the update_company_from_dnb_data command when a subset of DNB fields are updated.
    """
    company = CompanyFactory(duns_number='123456789')
    original_company = Company.objects.get(id=company.id)
    task_result = update_company_from_dnb_data.apply_async(
        args=[dnb_response_uk['results'][0]],
        kwargs={'fields_to_update': ['global_ultimate_duns_number']},
    )
    assert task_result.successful()
    company.refresh_from_db()
    assert model_to_dict(company) == {
        'address_1': original_company.address_1,
        'address_2': original_company.address_2,
        'address_country': original_company.address_country_id,
        'address_county': original_company.address_county,
        'address_postcode': original_company.address_postcode,
        'address_town': original_company.address_town,
        'archived': original_company.archived,
        'archived_by': original_company.archived_by,
        'archived_documents_url_path': original_company.archived_documents_url_path,
        'archived_on': original_company.archived_on,
        'archived_reason': original_company.archived_reason,
        'business_type': original_company.business_type_id,
        'company_number': original_company.company_number,
        'created_by': original_company.created_by_id,
        'description': original_company.description,
        'dnb_investigation_data': original_company.dnb_investigation_data,
        'duns_number': original_company.duns_number,
        'employee_range': original_company.employee_range_id,
        'export_experience_category': original_company.export_experience_category_id,
        'export_potential': original_company.export_potential,
        'export_to_countries': [],
        'future_interest_countries': [],
        'global_headquarters': original_company.global_headquarters,
        'global_ultimate_duns_number': '291332174',
        'great_profile_status': original_company.great_profile_status,
        'headquarter_type': original_company.headquarter_type,
        'id': original_company.id,
        'is_number_of_employees_estimated': original_company.is_number_of_employees_estimated,
        'is_turnover_estimated': original_company.is_turnover_estimated,
        'modified_by': original_company.modified_by_id,
        'name': original_company.name,
        'number_of_employees': original_company.number_of_employees,
        'one_list_account_owner': original_company.one_list_account_owner,
        'one_list_tier': original_company.one_list_tier,
        'pending_dnb_investigation': original_company.pending_dnb_investigation,
        'reference_code': original_company.reference_code,
        'registered_address_1': original_company.registered_address_1,
        'registered_address_2': original_company.registered_address_2,
        'registered_address_country': original_company.registered_address_country_id,
        'registered_address_county': original_company.registered_address_county,
        'registered_address_postcode': original_company.registered_address_postcode,
        'registered_address_town': original_company.registered_address_town,
        'sector': original_company.sector_id,
        'trading_names': original_company.trading_names,
        'transfer_reason': original_company.transfer_reason,
        'transferred_by': None,
        'transferred_on': None,
        'transferred_to': None,
        'turnover': original_company.turnover,
        'turnover_range': original_company.turnover_range_id,
        'uk_region': original_company.uk_region_id,
        'vat_number': original_company.vat_number,
        'website': original_company.website,
        'dnb_modified_on': now(),
    }


@freeze_time('2019-01-01 11:12:13')
def test_update_company_from_dnb_data_does_not_exist(dnb_response_uk, caplog):
    """
    Test the update_company_from_dnb_data command when the company does not exist in Data Hub.
    """
    task_result = update_company_from_dnb_data.apply_async(args=[dnb_response_uk['results'][0]])
    assert not task_result.successful()
    assert 'Company matching duns_number was not found' in caplog.text


@freeze_time('2019-01-01 11:12:13')
def test_update_company_from_dnb_data_fails_validation(dnb_response_uk, caplog):
    """
    Test the update_company_from_dnb_data command when the company data does not pass validation
    checks.
    """
    CompanyFactory(duns_number='123456789')
    dnb_response_uk['results'][0]['primary_name'] = 'a' * 9999
    task_result = update_company_from_dnb_data.apply_async(args=[dnb_response_uk['results'][0]])
    assert not task_result.successful()
    assert 'Data from D&B did not pass the Data Hub validation checks.' in caplog.text
