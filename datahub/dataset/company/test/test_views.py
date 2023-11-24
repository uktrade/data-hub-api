from datetime import datetime

import pytest
from django.urls import reverse
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status

from datahub.company.test.factories import (
    ArchivedCompanyFactory,
    CompanyFactory,
    CompanyWithAreaFactory,
    OneListCoreTeamMemberFactory,
    SubsidiaryFactory,
)
from datahub.core.test_utils import format_date_or_datetime, get_attr_or_default, get_attr_or_none
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.metadata.utils import convert_usd_to_gbp


def get_expected_data_from_company(company):
    """Returns company data as a dictionary"""
    data = {
        'address_1': company.address_1,
        'address_2': company.address_2,
        'address_county': company.address_county,
        'address_country__name': company.address_country.name,
        'address_postcode': company.address_postcode,
        'address_area__name': get_attr_or_none(
            company,
            'address_area.name',
        ),
        'address_town': company.address_town,
        'archived': company.archived,
        'archived_on': format_date_or_datetime(company.archived_on),
        'archived_reason': company.archived_reason,
        'business_type__name': get_attr_or_none(company, 'business_type.name'),
        'company_number': company.company_number,
        'created_by_id': (str(company.created_by_id) if company.created_by is not None else None),
        'created_on': format_date_or_datetime(company.created_on),
        'description': company.description,
        'duns_number': company.duns_number,
        'export_experience_category__name': get_attr_or_none(
            company,
            'export_experience_category.name',
        ),
        'global_headquarters_id': (
            str(company.global_headquarters_id)
            if company.global_headquarters_id is not None
            else None
        ),
        'global_ultimate_duns_number': company.global_ultimate_duns_number,
        'headquarter_type__name': get_attr_or_none(
            'company',
            'headquarter_type.name',
        ),
        'id': str(company.id),
        'is_number_of_employees_estimated': company.is_number_of_employees_estimated,
        'is_turnover_estimated': company.is_turnover_estimated,
        'modified_on': format_date_or_datetime(company.modified_on),
        'name': company.name,
        'number_of_employees': company.number_of_employees,
        'one_list_tier__name': get_attr_or_none(company, 'one_list_tier.name'),
        'one_list_core_team_advisers': get_attr_or_default(
            company,
            'one_list_core_team_advisers',
            [None],
        ),
        'one_list_account_owner_id': company.one_list_account_owner_id,
        'reference_code': company.reference_code,
        'registered_address_1': company.registered_address_1,
        'registered_address_2': company.registered_address_2,
        'registered_address_country__name': get_attr_or_none(
            company,
            'registered_address_country.name',
        ),
        'registered_address_county': company.registered_address_county,
        'registered_address_postcode': company.registered_address_postcode,
        'registered_address_area__name': get_attr_or_none(
            company,
            'registered_address_area.name',
        ),
        'registered_address_town': company.registered_address_town,
        'sector_name': get_attr_or_none(company, 'sector.name'),
        'export_segment': company.export_segment,
        'export_sub_segment': company.export_sub_segment,
        'trading_names': company.trading_names,
        'turnover': company.turnover,
        'uk_region__name': get_attr_or_none(company, 'uk_region.name'),
        'vat_number': company.vat_number,
        'website': company.website,
        'is_out_of_business': company.is_out_of_business,
        'strategy': company.strategy,
    }
    if data['turnover'] is not None:
        data['turnover_gbp'] = convert_usd_to_gbp(data['turnover'])
    else:
        data['turnover_gbp'] = None

    return data


@pytest.mark.django_db
class TestCompaniesDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for CompaniesDatasetView
    """

    view_url = reverse('api-v4:dataset:companies-dataset')
    factory = CompanyWithAreaFactory

    @pytest.mark.parametrize(
        'company_factory',
        (
            CompanyWithAreaFactory,
            ArchivedCompanyFactory,
        ),
    )
    def test_success(self, data_flow_api_client, company_factory):
        """Test that endpoint returns with expected data for a single company"""
        company = company_factory()
        company.created_by = None
        company.created_on = None
        company.save()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_company(company)
        assert result == expected_result

    @pytest.mark.parametrize(
        'company_factory',
        (
            CompanyWithAreaFactory,
            ArchivedCompanyFactory,
        ),
    )
    def test_core_team_member(self, data_flow_api_client, company_factory):
        """Test that endpoint returns with advisers on the core team"""
        company = company_factory()
        company.one_list_core_team_advisers = [
            str(o.adviser.id)
            for o in OneListCoreTeamMemberFactory.create_batch(
                3,
                company=company,
            )
        ]
        company.save()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_company(company)
        assert result == expected_result

    @pytest.mark.parametrize(
        'company_factory',
        (
            CompanyWithAreaFactory,
            ArchivedCompanyFactory,
        ),
    )
    def test_turnover_null(self, data_flow_api_client, company_factory):
        """Test that endpoint returns with expected data for a null turnover value"""
        company = company_factory()
        company.created_by = None
        company.created_on = None
        company.turnover = None
        company.save()

        response = data_flow_api_client.get(self.view_url)

        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']

        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_company(company)
        assert result == expected_result

    @pytest.mark.parametrize(
        'company_factory',
        (
            CompanyWithAreaFactory,
            ArchivedCompanyFactory,
        ),
    )
    def test_turnover_negative(self, data_flow_api_client, company_factory):
        """Test that endpoint returns with expected data for a null turnover value"""
        company = company_factory()
        company.created_by = None
        company.created_on = None
        company.turnover = -1000
        company.save()

        response = data_flow_api_client.get(self.view_url)

        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']

        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_company(company)
        assert result == expected_result

    def test_success_subsidiary(self, data_flow_api_client):
        """Test that for a company and it's subsidiary two companies are returned"""
        company = SubsidiaryFactory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        result = next((x for x in response_results if x['id'] == str(company.id)))
        assert result == get_expected_data_from_company(company)

    def test_with_multiple_records(self, data_flow_api_client):
        """Test that endpoint returns correct number of records"""
        with freeze_time('2019-01-01 12:30:00'):
            company1 = CompanyFactory()
        with freeze_time('2019-01-03 12:00:00'):
            company2 = CompanyFactory()
        with freeze_time('2019-01-01 12:00:00'):
            company3 = CompanyFactory()
            company4 = CompanyFactory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_list = sorted([company3, company4], key=lambda x: x.pk) + [company1, company2]
        for index, company in enumerate(expected_list):
            assert str(company.id) == response_results[index]['id']

    def test_with_updated_since_filter(self, data_flow_api_client):
        """Test that the endpoint returns only companies created after a certain date"""
        # Create companies with different `created_on` dates
        CompanyFactory(created_on=datetime(2020, 1, 1, tzinfo=utc))
        company_after = CompanyFactory(created_on=datetime(2020, 6, 1, tzinfo=utc))

        # Define the `updated_since` date
        updated_since_date = datetime(2020, 2, 1, tzinfo=utc).strftime('%Y-%m-%d')

        # Make the request with the `updated_since` parameter
        response = data_flow_api_client.get(self.view_url, {'updated_since': updated_since_date})

        assert response.status_code == status.HTTP_200_OK

        # Check that only companies created after the `updated_since` date are returned
        expected_ids = [str(company_after.id)]
        response_ids = [company['id'] for company in response.json()['results']]

        assert response_ids == expected_ids
