from urllib.parse import urljoin

import pytest
from django.conf import settings
from django.utils.timezone import now
from freezegun import freeze_time

from datahub.company.models import Company
from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.dnb_api.link_company import CompanyAlreadyDNBLinkedException, link_company_with_dnb
from datahub.dnb_api.test.utils import model_to_dict_company
from datahub.dnb_api.utils import DNBServiceInvalidRequest
from datahub.metadata.models import Country

pytestmark = pytest.mark.django_db


DNB_SEARCH_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'companies/search/')


@freeze_time('2019-01-01 11:12:13')
def test_link_company_with_dnb_success(
    requests_mock,
    dnb_response_uk,
    base_company_dict,
):
    """
    Test the link_company_with_dnb utility.
    """
    requests_mock.post(
        DNB_SEARCH_URL,
        json=dnb_response_uk,
    )
    company = CompanyFactory()
    original_company = Company.objects.get(id=company.id)
    modifying_adviser = AdviserFactory()
    link_company_with_dnb(company.id, '123456789', modifying_adviser)
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
        'modified_by': modifying_adviser.id,
        'name': 'FOO BICYCLE LIMITED',
        'is_number_of_employees_estimated': True,
        'number_of_employees': 260,
        'pending_dnb_investigation': False,
        'reference_code': '',
        'registered_address_area': None,
        'sector': original_company.sector_id,
        'export_segment': original_company.export_segment,
        'export_sub_segment': original_company.export_sub_segment,
        'turnover': 50651895,
        'turnover_range': original_company.turnover_range_id,
        'uk_region': original_company.uk_region_id,
        'dnb_modified_on': now(),
    }


def test_link_company_with_dnb_duns_already_set():
    """
    Test link_company_with_dnb when it is called for a company which has already
    been linked with a DNB record.
    """
    company = CompanyFactory(duns_number='123456788')
    modifying_adviser = AdviserFactory()
    with pytest.raises(CompanyAlreadyDNBLinkedException):
        link_company_with_dnb(company.id, '123456789', modifying_adviser)


def test_link_company_with_dnb_sync_task_failure(
    requests_mock,
    dnb_response_uk,
):
    """
    Test link_company_with_dnb when the sync_company_with_dnb task encounters
    a failure - expect the exception to bubble up.
    """
    malformed_response = dnb_response_uk.copy()
    del malformed_response['results']
    requests_mock.post(
        DNB_SEARCH_URL,
        json=malformed_response,
    )
    company = CompanyFactory()
    original_company = Company.objects.get(id=company.id)
    modifying_adviser = AdviserFactory()
    with pytest.raises(DNBServiceInvalidRequest):
        link_company_with_dnb(company.id, '123456789', modifying_adviser)
    company.refresh_from_db()
    # Ensure that any changes to the record were rolled back due to the task failure
    assert company.duns_number is None
    assert company.modified_by == original_company.modified_by
