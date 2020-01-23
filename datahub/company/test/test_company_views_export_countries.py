import random
import uuid
from operator import attrgetter, itemgetter

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import CompanyExportCountry, OneListTier
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyExportCountryFactory,
    CompanyFactory,
)
from datahub.core.constants import Country
from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime
from datahub.metadata.models import Country as CountryModel


class TestCompaniesToCompanyExportCountryModel(APITestMixin):
    """Tests for copying export countries from company model to CompanyExportCountry model"""

    def test_get_company_with_export_countries(self):
        """Tests the company item view."""
        ghq = CompanyFactory(
            global_headquarters=None,
            one_list_tier=OneListTier.objects.first(),
            one_list_account_owner=AdviserFactory(),
        )
        company = CompanyFactory(
            company_number='123',
            trading_names=['Xyz trading', 'Abc trading'],
            global_headquarters=ghq,
            one_list_tier=None,
            one_list_account_owner=None,
        )
        export_country_one, export_country_two = CompanyExportCountryFactory.create_batch(2)
        company.export_countries.set([export_country_one, export_country_two])
        user = create_test_user(
            permission_codenames=(
                'view_company',
                'view_company_document',
            ),
        )
        api_client = self.create_api_client(user=user)

        url = reverse('api-v4:company:item', kwargs={'pk': company.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': str(company.pk),
            'created_on': format_date_or_datetime(company.created_on),
            'modified_on': format_date_or_datetime(company.modified_on),
            'name': company.name,
            'reference_code': company.reference_code,
            'company_number': company.company_number,
            'vat_number': company.vat_number,
            'duns_number': company.duns_number,
            'trading_names': company.trading_names,
            'address': {
                'line_1': company.address_1,
                'line_2': company.address_2 or '',
                'town': company.address_town,
                'county': company.address_county or '',
                'postcode': company.address_postcode or '',
                'country': {
                    'id': str(company.address_country.id),
                    'name': company.address_country.name,
                },
            },
            'registered_address': {
                'line_1': company.registered_address_1,
                'line_2': company.registered_address_2 or '',
                'town': company.registered_address_town,
                'county': company.registered_address_county or '',
                'postcode': company.registered_address_postcode or '',
                'country': {
                    'id': str(company.registered_address_country.id),
                    'name': company.registered_address_country.name,
                },
            },
            'uk_based': (
                company.address_country.id == uuid.UUID(Country.united_kingdom.value.id)
            ),
            'uk_region': {
                'id': str(company.uk_region.id),
                'name': company.uk_region.name,
            },
            'business_type': {
                'id': str(company.business_type.id),
                'name': company.business_type.name,
            },
            'contacts': [],
            'description': company.description,
            'employee_range': {
                'id': str(company.employee_range.id),
                'name': company.employee_range.name,
            },
            'number_of_employees': company.number_of_employees,
            'is_number_of_employees_estimated': company.is_number_of_employees_estimated,
            'export_experience_category': {
                'id': str(company.export_experience_category.id),
                'name': company.export_experience_category.name,
            },
            'export_potential': None,
            'great_profile_status': None,
            'export_to_countries': [],
            'future_interest_countries': [],
            'headquarter_type': company.headquarter_type,
            'sector': {
                'id': str(company.sector.id),
                'name': company.sector.name,
            },
            'turnover_range': {
                'id': str(company.turnover_range.id),
                'name': company.turnover_range.name,
            },
            'turnover': company.turnover,
            'is_turnover_estimated': company.is_turnover_estimated,
            'website': company.website,
            'global_headquarters': {
                'id': str(ghq.id),
                'name': ghq.name,
            },
            'one_list_group_tier': {
                'id': str(ghq.one_list_tier.id),
                'name': ghq.one_list_tier.name,
            },
            'one_list_group_global_account_manager': {
                'id': str(ghq.one_list_account_owner.pk),
                'name': ghq.one_list_account_owner.name,
                'first_name': ghq.one_list_account_owner.first_name,
                'last_name': ghq.one_list_account_owner.last_name,
                'contact_email': ghq.one_list_account_owner.contact_email,
                'dit_team': {
                    'id': str(ghq.one_list_account_owner.dit_team.id),
                    'name': ghq.one_list_account_owner.dit_team.name,
                    'uk_region': {
                        'id': str(ghq.one_list_account_owner.dit_team.uk_region.pk),
                        'name': ghq.one_list_account_owner.dit_team.uk_region.name,
                    },
                    'country': {
                        'id': str(ghq.one_list_account_owner.dit_team.country.pk),
                        'name': ghq.one_list_account_owner.dit_team.country.name,
                    },
                },
            },
            'export_countries': [
                {
                    'country': {
                        'id': str(item.country.pk),
                        'name': item.country.name,
                    },
                    'status': item.status,
                } for item in company.export_countries.order_by('pk')
            ],
            'archived_documents_url_path': company.archived_documents_url_path,
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'transferred_by': None,
            'transferred_on': None,
            'transferred_to': None,
            'transfer_reason': '',
            'pending_dnb_investigation': False,
            'is_global_ultimate': company.is_global_ultimate,
            'global_ultimate_duns_number': company.global_ultimate_duns_number,
            'dnb_modified_on': company.dnb_modified_on,
        }

    @staticmethod
    def update_company_export_country_model(*, self, new_countries, field, company, model_status):
        """
        Standard action for updating the model with
        the given data and returning the actual response

        :param self: current class scope
        :param new_countries: countries to be added to the model
        :param field: model field to update
        :param company:
        :param model_status: status of the field (currently_exporting || future_interest)
        :return: {
            'status_code': http response code type (200, 404 etc),
            'countries': countries recorded in the model against the current company,
            'country_ids': and their corresponding id's
        }
        """
        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                field: [country.id for country in new_countries],
            },
        )
        response_data = response.json()

        response_data[field].sort(key=itemgetter('id'))
        new_countries.sort(key=attrgetter('pk'))

        actual_response_country_ids = [
            country['id'] for country in response_data[field]
        ]

        actual_export_countries = CompanyExportCountry.objects.filter(
            company=company,
            status=model_status,
        ).order_by(
            'country__pk',
        )

        # return response, actual_export_countries, actual_response_country_ids
        return {
            'status_code': response.status_code,
            'countries': actual_export_countries,
            'country_ids': actual_response_country_ids,
        }

    @pytest.mark.parametrize(
        'field,model_status',
        (
            (
                'export_to_countries',
                CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting,
            ),
            (
                'future_interest_countries',
                CompanyExportCountry.EXPORT_INTEREST_STATUSES.future_interest,
            ),
        ),
    )
    def test_adding_to_empty_company_export_to_country_model(
            self,
            field,
            model_status,
    ):
        """Test adding export countries to an empty CompanyExportCountry model"""
        company = CompanyFactory(
            **{field: []},
        )
        new_countries = list(CountryModel.objects.order_by('?')[:2])

        # now update them
        response_data = self.update_company_export_country_model(
            self=self,
            new_countries=new_countries,
            field=field,
            company=company,
            model_status=model_status,
        )

        assert response_data['status_code'] == status.HTTP_200_OK
        assert response_data['country_ids'] == [str(country.pk) for country in new_countries]
        assert [
            export_country.country for export_country in response_data['countries']
        ] == new_countries

    @pytest.mark.parametrize(
        'field,model_status',
        (
            (
                'export_to_countries',
                CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting,
            ),
            (
                'future_interest_countries',
                CompanyExportCountry.EXPORT_INTEREST_STATUSES.future_interest,
            ),
        ),
    )
    def test_changing_company_export_to_country_model(
            self,
            field,
            model_status,
    ):
        """Test changing export countries to completely new ones on CompanyExportCountry model"""
        existing_countries = list(CountryModel.objects.order_by('?')[:random.randint(1, 10)])
        # initialise the models in scope
        company = CompanyFactory(
            **{
                field: existing_countries,
            },
        )

        for country in existing_countries:
            CompanyExportCountryFactory(
                country=country,
                company=company,
                status=model_status,
            )

        random_countries = list(CountryModel.objects.order_by('?')[:random.randint(1, 10)])
        new_countries = [country for country in random_countries
                         if country not in existing_countries]

        # now update them
        response_data = self.update_company_export_country_model(
            self=self,
            new_countries=new_countries,
            field=field,
            company=company,
            model_status=model_status,
        )

        assert response_data['status_code'] == status.HTTP_200_OK
        assert response_data['country_ids'] == [str(country.pk) for country in new_countries]
        assert [
            export_country.country for export_country in response_data['countries']
        ] == new_countries

    @pytest.mark.parametrize(
        'field,model_status',
        (
            (
                'export_to_countries',
                CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting,
            ),
            (
                'future_interest_countries',
                CompanyExportCountry.EXPORT_INTEREST_STATUSES.future_interest,
            ),
        ),
    )
    def test_appending_new_items_to_existing_ones_in_company_export_to_country_model(
            self,
            field,
            model_status,
    ):
        """
        Test appending new export countries to
        an existing items in CompanyExportCountry model
        """
        existing_countries = list(CountryModel.objects.order_by('?')[:random.randint(1, 10)])
        # initialise the models in scope
        company = CompanyFactory(
            **{
                field: existing_countries,
            },
        )

        for country in existing_countries:
            CompanyExportCountryFactory(
                country=country,
                company=company,
                status=model_status,
            )

        new_countries = existing_countries + list(CountryModel.objects.order_by('?')[:0])

        # now update them
        response_data = self.update_company_export_country_model(
            self=self,
            new_countries=new_countries,
            field=field,
            company=company,
            model_status=model_status,
        )

        assert response_data['status_code'] == status.HTTP_200_OK
        assert response_data['country_ids'] == [str(country.pk) for country in new_countries]
        assert [
            export_country.country for export_country in response_data['countries']
        ] == new_countries

    def test_adding_overlapping_countries_in_company_export_to_country_model(self):
        """
        Test adding overlapping countries to CompanyExportCountry model
        Priority takes currently exporting to countries over
        future countries of interest
        """
        initial_countries = list(CountryModel.objects.order_by('?')[:5])
        initial_export_to_countries = initial_countries[:3]
        initial_future_interest_countries = initial_countries[3:]

        # initialise the models in scope
        company = CompanyFactory(
            export_to_countries=initial_export_to_countries,
            future_interest_countries=initial_future_interest_countries,
        )

        for country in initial_future_interest_countries:
            CompanyExportCountryFactory(
                country=country,
                company=company,
                status=CompanyExportCountry.EXPORT_INTEREST_STATUSES.future_interest,
            )

        for country in initial_export_to_countries:
            CompanyExportCountryFactory(
                country=country,
                company=company,
                status=CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting,
            )

        new_countries = list(CountryModel.objects.order_by('?')[:5])
        new_export_to_countries = new_countries[:2]
        new_future_interest_countries = new_countries[:3]

        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'export_to_countries': [country.id for country in new_export_to_countries],
                'future_interest_countries': [
                    country.id for country in new_future_interest_countries
                ],
            },
        )

        response_data = response.json()

        response_data['export_to_countries'].sort(key=itemgetter('id'))
        response_data['future_interest_countries'].sort(key=itemgetter('id'))

        new_export_to_countries.sort(key=attrgetter('pk'))

        actual_response_export_to_country_ids = [
            country['id'] for country in response_data['export_to_countries']
        ]

        actual_export_to_countries = CompanyExportCountry.objects.filter(
            company=company,
            status=CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting,
        ).order_by(
            'country__pk',
        )

        actual_future_interest_countries = CompanyExportCountry.objects.filter(
            company=company,
            status=CompanyExportCountry.EXPORT_INTEREST_STATUSES.future_interest,
        ).order_by(
            'country__pk',
        )

        assert response.status_code == status.HTTP_200_OK
        assert actual_response_export_to_country_ids == [
            str(country.pk) for country in new_export_to_countries
        ]
        assert [
            export_country.country for export_country in actual_export_to_countries
        ] == new_export_to_countries
        assert [
            list(actual_future_interest_countries)[0].country,
        ] == list(set(new_future_interest_countries) - set(new_export_to_countries))
