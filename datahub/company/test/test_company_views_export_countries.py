import random
from operator import attrgetter, itemgetter

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import CompanyExportCountry
from datahub.company.test.factories import CompanyExportCountryFactory, CompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.metadata.models import Country as CountryModel


class TestCompaniesToCompanyExportCountryModel(APITestMixin):
    """Tests for copying export countries from company model to CompanyExportCountry model"""

    def test_get_company_with_export_countries(self):
        """
        Tests the company response has export countries that are
        in the new CompanyExportCountry model.
        """
        company = CompanyFactory()
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
        assert response.json().get('export_countries', []) is not []
        export_countries_response = response.json().get('export_countries')
        assert export_countries_response == [
            {
                'country': {
                    'id': str(item.country.pk),
                    'name': item.country.name,
                },
                'status': item.status,
            } for item in company.export_countries.order_by('pk')
        ]

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
