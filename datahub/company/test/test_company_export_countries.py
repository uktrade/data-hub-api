import random
from operator import attrgetter, itemgetter

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import CompanyExportCountry
from datahub.company.test.factories import CompanyExportCountryFactory, CompanyFactory
from datahub.core.constants import (
    Country,
    INTERACTION_ADD_COUNTRIES,
)
from datahub.core.test_utils import APITestMixin
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.metadata.models import Country as CountryModel


class TestCompanyExportCountryModel(APITestMixin):
    """Tests for copying export countries from company model to CompanyExportCountry model"""

    @staticmethod
    def update_company_fields(*, self, new_countries, field, company, model_status):
        """
        Standard action for updating the Company model with
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
        response_data = self.update_company_fields(
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
        response_data = self.update_company_fields(
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
        response_data = self.update_company_fields(
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

    def test_edit_company_fields_check_not_interested_is_intact(self):
        """
        Check when in case feature flag is switched OFF
        and updating old export country fields will not wipe off
        not_interested countries in `CompanyExportCountry` model.
        """
        initial_countries = list(CountryModel.objects.order_by('?')[:5])
        company = CompanyFactory()
        CompanyExportCountry(
            country=initial_countries[0],
            company=company,
            status=CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting,
        ).save()
        CompanyExportCountry(
            country=initial_countries[1],
            company=company,
            status=CompanyExportCountry.EXPORT_INTEREST_STATUSES.future_interest,
        ).save()
        CompanyExportCountry(
            country=initial_countries[2],
            company=company,
            status=CompanyExportCountry.EXPORT_INTEREST_STATUSES.not_interested,
        ).save()

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
        assert response.status_code == status.HTTP_200_OK
        not_interested = company.export_countries.filter(
            status=CompanyExportCountry.EXPORT_INTEREST_STATUSES.not_interested,
        )
        assert len(not_interested) == 1
        assert not_interested[0].country == initial_countries[2]

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        'flag,data,expected_error',
        (
            # can't send export_to_countries, future_interest_countries when flag is active
            (
                True,
                {
                    'export_to_countries': None,
                    'future_interest_countries': None,
                },
                {
                    'export_to_countries': ['This field may not be null.'],
                    'future_interest_countries': ['This field may not be null.'],
                },
            ),
            (
                True,
                {
                    'export_to_countries': [],
                    'future_interest_countries': [],
                },
                {
                    'export_to_countries': ['Invalid field.'],
                    'future_interest_countries': ['Invalid field.'],
                },
            ),
            (
                True,
                {
                    'export_to_countries': [
                        Country.canada.value.id,
                        Country.greece.value.id,
                    ],
                    'future_interest_countries': [
                        Country.united_states.value.id,
                        Country.azerbaijan.value.id,
                    ],
                },
                {
                    'export_to_countries': ['Invalid field.'],
                    'future_interest_countries': ['Invalid field.'],
                },
            ),
            # can't send export_countries when flag is inactive
            (
                False,
                {
                    'export_countries': None,
                },
                {'export_countries': ['This field may not be null.']},
            ),
            (
                False,
                {
                    'export_countries': [],
                },
                {'export_countries': ['Invalid field.']},
            ),
            (
                False,
                {
                    'export_countries': [
                        {
                            'country': {
                                'id': Country.canada.value.id,
                            },
                            'status':
                                CompanyExportCountry.EXPORT_INTEREST_STATUSES.future_interest,
                        },
                    ],
                },
                {'export_countries': ['Invalid field.']},
            ),
            # can't add duplicate countries with export_countries
            (
                True,
                {
                    'export_countries': [
                        {
                            'country': {
                                'id': Country.canada.value.id,
                            },
                            'status':
                                CompanyExportCountry.EXPORT_INTEREST_STATUSES.future_interest,
                        },
                        {
                            'country': {
                                'id': Country.canada.value.id,
                            },
                            'status':
                                CompanyExportCountry.EXPORT_INTEREST_STATUSES.not_interested,
                        },
                    ],
                },
                {
                    'non_field_errors':
                        ['A country that was discussed cannot be entered in multiple fields.'],
                },
            ),
            # export_countries must be fully formed. status must be a valid choice
            (
                True,
                {
                    'export_countries': [
                        {
                            'country': {
                                'id': Country.canada.value.id,
                            },
                            'status': 'foobar',
                        },
                    ],
                },
                {
                    'export_countries': [{'status': ['"foobar" is not a valid choice.']}],
                },
            ),
            # export_countries must be fully formed. country ID must be a valid UUID
            (
                True,
                {
                    'export_countries': [
                        {
                            'country': {
                                'id': '1234',
                            },
                            'status':
                                CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting,
                        },
                    ],
                },
                {
                    'export_countries': [{'country': ['Must be a valid UUID.']}],
                },
            ),
            # export_countries must be fully formed. country UUID must be a valid Country
            (
                True,
                {
                    'export_countries': [
                        {
                            'country': {
                                'id': '4dee26c2-799d-49a8-a533-c30c595c942c',
                            },
                            'status':
                                CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting,
                        },
                    ],
                },
                {
                    'export_countries': [
                        {
                            'country': [
                                'Invalid pk "4dee26c2-799d-49a8-a533-c30c595c942c"'
                                ' - object does not exist.',
                            ],
                        },
                    ],
                },
            ),
        ),
    )
    def test_validation_error(self, flag, data, expected_error):
        """Test validation scenarios."""
        FeatureFlagFactory(code=INTERACTION_ADD_COUNTRIES, is_active=flag)
        company = CompanyFactory(
            registered_address_1='',
            registered_address_2='',
            registered_address_town='',
            registered_address_county='',
            registered_address_postcode='',
            registered_address_country_id=None,
        )

        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    def _get_export_interest_status(self):
        export_interest_statuses = [
            CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting,
            CompanyExportCountry.EXPORT_INTEREST_STATUSES.future_interest,
            CompanyExportCountry.EXPORT_INTEREST_STATUSES.not_interested,
        ]
        return random.choice(export_interest_statuses)

    def test_update_company_with_export_countries(self):
        """
        Test company export countries update.
        """
        FeatureFlagFactory(code=INTERACTION_ADD_COUNTRIES, is_active=True)
        company = CompanyFactory()

        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})

        data = {
            'export_countries': [
                {
                    'country': {
                        'id': Country.canada.value.id,
                        'name': Country.canada.value.name,
                    },
                    'status':
                        CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting,
                },
            ],
        }

        response = self.api_client.patch(url, data=data)
        assert response.status_code == status.HTTP_200_OK

        export_countries = company.export_countries.all()
        assert export_countries.count() == 1
        assert str(export_countries[0].country.id) == Country.canada.value.id
        currently_exporting = CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting
        assert export_countries[0].status == currently_exporting

    def test_update_company_with_export_countries_sync_company_fields(self):
        """
        Test company export countries update
        should sync to company fields, currently_exporting_to and future_interest_countries.
        """
        company = CompanyFactory()

        FeatureFlagFactory(code=INTERACTION_ADD_COUNTRIES, is_active=True)

        countries_set = list(CountryModel.objects.order_by('name')[:10])
        data_items = [
            {
                'country': {
                    'id': str(country.id),
                    'name': country.name,
                },
                'status': self._get_export_interest_status(),
            }
            for country in countries_set
        ]
        data = {
            'export_countries': data_items,
        }

        status_wise_items = {
            outer['status']: [
                inner['country']['id']
                for inner in data_items if inner['status'] == outer['status']
            ] for outer in data_items
        }
        current_countries_request = status_wise_items[
            CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting
        ]
        future_countries_request = status_wise_items[
            CompanyExportCountry.EXPORT_INTEREST_STATUSES.future_interest
        ]

        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, data=data)
        assert response.status_code == status.HTTP_200_OK

        company.refresh_from_db()
        current_countries_response = [
            str(c.id) for c in company.export_to_countries.all()
        ]

        future_countries_response = [
            str(c.id) for c in company.future_interest_countries.all()
        ]

        assert current_countries_request == current_countries_response
        assert future_countries_request == future_countries_response

    def test_update_company_with_pre_existing_company_fields_sync(self):
        """
        Test sync when company export_countries update, of a company with
        currently_exporting_to and future_interest_countries preset.
        """
        initial_countries = list(CountryModel.objects.order_by('?')[:5])
        initial_export_to_countries = initial_countries[:3]
        initial_future_interest_countries = initial_countries[3:]

        company = CompanyFactory(
            export_to_countries=initial_export_to_countries,
            future_interest_countries=initial_future_interest_countries,
        )

        FeatureFlagFactory(code=INTERACTION_ADD_COUNTRIES, is_active=True)
        countries_set = list(CountryModel.objects.order_by('name')[:10])
        data_items = [
            {
                'country': {
                    'id': str(country.id),
                    'name': country.name,
                },
                'status': self._get_export_interest_status(),
            }
            for country in countries_set
        ]
        data = {
            'export_countries': data_items,
        }

        status_wise_items = {
            outer['status']: [
                inner['country']['id']
                for inner in data_items if inner['status'] == outer['status']
            ] for outer in data_items
        }
        current_countries_request = status_wise_items[
            CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting
        ]
        future_countries_request = status_wise_items[
            CompanyExportCountry.EXPORT_INTEREST_STATUSES.future_interest
        ]

        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, data=data)
        assert response.status_code == status.HTTP_200_OK

        company.refresh_from_db()
        current_countries_response = [
            str(c.id) for c in company.export_to_countries.all()
        ]

        future_countries_response = [
            str(c.id) for c in company.future_interest_countries.all()
        ]

        assert current_countries_request == current_countries_response
        assert future_countries_request == future_countries_response

    def test_get_company_with_export_countries(self):
        """Test get company details after updating export countries."""
        FeatureFlagFactory(code=INTERACTION_ADD_COUNTRIES, is_active=True)
        company = CompanyFactory()

        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})

        countries_set = list(CountryModel.objects.order_by('name')[:10])
        data_items = [
            {
                'country': {
                    'id': str(country.id),
                    'name': country.name,
                },
                'status': self._get_export_interest_status(),
            }
            for country in countries_set
        ]
        data = {
            'export_countries': data_items,
        }

        status_wise_items = {
            outer['status']: [
                inner['country']['id']
                for inner in data_items if inner['status'] == outer['status']
            ] for outer in data_items
        }

        response = self.api_client.patch(url, data=data)
        assert response.status_code == status.HTTP_200_OK

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        response_data['export_countries'].sort(key=lambda item: item['country']['name'])
        current_countries_request = status_wise_items[
            CompanyExportCountry.EXPORT_INTEREST_STATUSES.currently_exporting
        ]
        current_countries_response = [c['id'] for c in response_data['export_to_countries']]

        future_countries_request = status_wise_items[
            CompanyExportCountry.EXPORT_INTEREST_STATUSES.future_interest
        ]
        future_countries_response = [c['id'] for c in response_data['future_interest_countries']]

        assert response_data['export_countries'] == data['export_countries']
        assert current_countries_request == current_countries_response
        assert future_countries_request == future_countries_response
