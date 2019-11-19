from unittest import mock
from urllib.parse import urljoin

import pytest
from celery.exceptions import Retry
from django.conf import settings
from django.forms.models import model_to_dict
from django.utils.timezone import now
from freezegun import freeze_time
from reversion.models import Version

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.dnb_api.tasks import sync_company_with_dnb
from datahub.dnb_api.utils import DNBServiceError
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
    'error_status_code,expect_retry',
    (
        (504, True),
        (503, True),
        (502, True),
        (500, True),
        (403, False),
        (400, False),
    ),
)
def test_sync_company_with_dnb_retries_errors(monkeypatch, error_status_code, expect_retry):
    """
    Test the sync_company_with_dnb task retries server errors.
    """
    company = CompanyFactory(duns_number='123456789')

    # Set up a DNBServiceError with the parametrized status code
    error = DNBServiceError('An error occurred', status_code=error_status_code)
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
