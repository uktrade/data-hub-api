import random
from operator import attrgetter, itemgetter

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import (
    CompanyExportCountry,
    CompanyExportCountryHistory,
    CompanyPermission,
)
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyExportCountryFactory,
    CompanyExportCountryHistoryFactory,
    CompanyFactory,
)
from datahub.core.constants import Country
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
)
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
                'view_companyexportcountry',
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

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if no credentials are provided."""
        company = CompanyFactory()
        url = reverse('api-v4:company:update-export-detail', kwargs={'pk': company.pk})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames',
        (
            (),
            (CompanyPermission.change_company,),
            ('change_companyexportcountry',),
        ),
    )
    def test_returns_403_if_without_permission(self, permission_codenames):
        """
        Test that a 403 is returned if the user does not have all of the required
        permissions.
        """
        company = CompanyFactory()
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:company:update-export-detail', kwargs={'pk': company.pk})

        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        'data,expected_error',
        (
            # can't add duplicate countries with export_countries
            (
                {
                    'export_countries': [
                        {
                            'country': {
                                'id': Country.canada.value.id,
                            },
                            'status':
                                CompanyExportCountry.Status.FUTURE_INTEREST,
                        },
                        {
                            'country': {
                                'id': Country.canada.value.id,
                            },
                            'status':
                                CompanyExportCountry.Status.NOT_INTERESTED,
                        },
                    ],
                },
                {
                    'non_field_errors':
                        ['You cannot enter the same country in multiple fields.'],
                },
            ),
            # export_countries must be fully formed. status must be a valid choice
            (
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
                {
                    'export_countries': [
                        {
                            'country': {
                                'id': '1234',
                            },
                            'status':
                                CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                        },
                    ],
                },
                {
                    'export_countries': [{'country': ['Must be a valid UUID.']}],
                },
            ),
            # export_countries must be fully formed. country UUID must be a valid Country
            (
                {
                    'export_countries': [
                        {
                            'country': {
                                'id': '4dee26c2-799d-49a8-a533-c30c595c942c',
                            },
                            'status':
                                CompanyExportCountry.Status.CURRENTLY_EXPORTING,
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
    def test_validation_error_export_country_api(
        self,
        data,
        expected_error,
    ):
        """Test validation scenarios."""
        company = CompanyFactory()

        url = reverse('api-v4:company:update-export-detail', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    def _get_export_interest_status(self):
        """Helper function to randomly select export status"""
        export_interest_statuses = [
            CompanyExportCountry.Status.CURRENTLY_EXPORTING,
            CompanyExportCountry.Status.FUTURE_INTEREST,
            CompanyExportCountry.Status.NOT_INTERESTED,
        ]
        return random.choice(export_interest_statuses)

    def test_update_company_with_export_countries(self):
        """
        Test company export countries update.
        """
        company = CompanyFactory()

        data = {
            'export_countries': [
                {
                    'country': {
                        'id': Country.canada.value.id,
                        'name': Country.canada.value.name,
                    },
                    'status':
                        CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                },
            ],
        }

        url = reverse('api-v4:company:update-export-detail', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, data=data)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        export_countries = company.export_countries.all()
        assert export_countries.count() == 1
        assert str(export_countries[0].country.id) == Country.canada.value.id
        currently_exporting = CompanyExportCountry.Status.CURRENTLY_EXPORTING
        assert export_countries[0].status == currently_exporting

    def test_update_company_with_export_countries_sync_company_fields(
        self,
    ):
        """
        Test company export countries update
        should sync to company fields, currently_exporting_to and future_interest_countries.
        """
        company = CompanyFactory()

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
        current_countries_request = status_wise_items.get(
            CompanyExportCountry.Status.CURRENTLY_EXPORTING,
            [],
        )
        future_countries_request = status_wise_items.get(
            CompanyExportCountry.Status.FUTURE_INTEREST,
            [],
        )

        url = reverse('api-v4:company:update-export-detail', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, data=data)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        company.refresh_from_db()
        current_countries_response = [
            str(c.id) for c in company.export_to_countries.all()
        ]

        future_countries_response = [
            str(c.id) for c in company.future_interest_countries.all()
        ]

        assert current_countries_request == current_countries_response
        assert future_countries_request == future_countries_response

    def test_update_company_export_countries_with_pre_existing_company_fields_sync(
        self,
    ):
        """
        Test sync when company export_countries update, of a company with
        currently_exporting_to and future_interest_countries preset.
        """
        initial_countries = list(CountryModel.objects.order_by('id')[:5])
        initial_export_to_countries = initial_countries[:3]
        initial_future_interest_countries = initial_countries[3:]

        company = CompanyFactory(
            export_to_countries=initial_export_to_countries,
            future_interest_countries=initial_future_interest_countries,
        )

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
        current_countries_request = status_wise_items.get(
            CompanyExportCountry.Status.CURRENTLY_EXPORTING,
            [],
        )
        future_countries_request = status_wise_items.get(
            CompanyExportCountry.Status.FUTURE_INTEREST,
            [],
        )

        url = reverse('api-v4:company:update-export-detail', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, data=data)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        company.refresh_from_db()
        current_countries_response = [
            str(c.id) for c in company.export_to_countries.all()
        ]

        future_countries_response = [
            str(c.id) for c in company.future_interest_countries.all()
        ]

        assert current_countries_request == current_countries_response
        assert future_countries_request == future_countries_response

    def test_update_company_export_countries_with_new_list_deletes_old_ones(
        self,
    ):
        """
        Test when updating company export countries with a new list
        and make sure old ones are removed.
        """
        company = CompanyFactory()
        new_countries = list(CountryModel.objects.order_by('id')[:3])
        CompanyExportCountryFactory(
            country=new_countries.pop(0),
            company=company,
        )

        input_data_items = [
            {
                'country': {
                    'id': str(country.id),
                    'name': country.name,
                },
                'status': self._get_export_interest_status(),
            }
            for country in new_countries
        ]
        input_export_countries = {
            'export_countries': input_data_items,
        }

        url = reverse('api-v4:company:update-export-detail', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, data=input_export_countries)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        company.refresh_from_db()
        company_data_items = [
            {
                'country': {
                    'id': str(export_country.country.id),
                    'name': export_country.country.name,
                },
                'status': export_country.status,
            }
            for export_country in company.export_countries.all().order_by('country__id')
        ]
        company_export_countries = {
            'export_countries': company_data_items,
        }
        assert company_export_countries == input_export_countries

    def test_update_company_export_countries_with_empty_list_deletes_all(
        self,
    ):
        """
        Test when updating company export countries with an empty list
        and make sure all items are removed.
        """
        company = CompanyFactory()
        export_country_one, export_country_two = CompanyExportCountryFactory.create_batch(2)
        company.export_countries.set([export_country_one, export_country_two])

        input_export_countries = {
            'export_countries': [],
        }

        url = reverse('api-v4:company:update-export-detail', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, data=input_export_countries)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        company.refresh_from_db()
        company_data_items = [
            {
                'country': {
                    'id': str(export_country.country.id),
                    'name': export_country.country.name,
                },
                'status': export_country.status,
            }
            for export_country in company.export_countries.all().order_by('country__id')
        ]
        company_export_countries = {
            'export_countries': company_data_items,
        }
        assert company_export_countries == input_export_countries

    def test_update_company_with_something_check_export_countries(
        self,
    ):
        """
        Test when updating company with something else other than export countries
        will not affect export countries.
        """
        company = CompanyFactory()
        export_country_one, export_country_two = CompanyExportCountryFactory.create_batch(2)
        company.export_countries.set([export_country_one, export_country_two])

        input_data = {
            'website': 'www.google.com',
        }

        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, data=input_data)
        assert response.status_code == status.HTTP_200_OK

        company.refresh_from_db()
        assert len(company.export_countries.all()) == 2

    def test_get_company(
        self,
    ):
        """Test get company details after updating export countries."""
        company = CompanyFactory()

        # Sorting in the database by name and sorting in Python by name can be different
        # due to collation/locale differences. Here we sort in the database to choose the
        # same 10 countries each run of the test, and then sort in Python to able to
        # compare with other Python-sorted lists later in the test
        countries_set = sorted(list(
            CountryModel.objects.order_by('name')[:10],
        ), key=lambda c: c.name)
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

        export_country_url = reverse(
            'api-v4:company:update-export-detail',
            kwargs={'pk': company.pk},
        )
        response = self.api_client.patch(export_country_url, data=data)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        company_url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.get(company_url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        response_data['export_countries'].sort(key=lambda item: item['country']['name'])
        current_countries_request = status_wise_items.get(
            CompanyExportCountry.Status.CURRENTLY_EXPORTING,
            [],
        )
        current_countries_response = [
            c['id'] for c in response_data.get('export_to_countries', [])
        ]

        future_countries_request = sorted(status_wise_items.get(
            CompanyExportCountry.Status.FUTURE_INTEREST,
            [],
        ))
        future_countries_response = sorted([
            c['id'] for c in response_data.get('future_interest_countries', [])
        ])

        assert response_data['export_countries'] == data['export_countries']
        assert current_countries_request == current_countries_response
        assert future_countries_request == future_countries_response

    def test_delete_company_export_countries_check_history_tracks_correct_user(self):
        """
        Check that history correctly tracks the user who deletes the export country
        """
        company = CompanyFactory()
        country = CountryModel.objects.order_by('name')[0]
        adviser = AdviserFactory()
        export_country = CompanyExportCountryFactory(
            company=company,
            country=country,
            status=CompanyExportCountry.Status.FUTURE_INTEREST,
            created_by=adviser,
        )
        CompanyExportCountryHistoryFactory(
            id=export_country.id,
            company=export_country.company,
            country=export_country.country,
            status=export_country.status,
            history_type=CompanyExportCountryHistory.HistoryType.INSERT,
            history_user=export_country.created_by,
        )

        new_user = create_test_user(
            permission_codenames=(
                'change_company',
                'change_companyexportcountry',
            ),
        )
        api_client = self.create_api_client(user=new_user)
        url = reverse('api-v4:company:update-export-detail', kwargs={'pk': company.pk})
        response = api_client.patch(
            url,
            data={
                'export_countries': [],
            },
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        company.refresh_from_db()
        assert company.export_countries.count() == 0
        delete_history = CompanyExportCountryHistory.objects.filter(
            company=company,
            history_type=CompanyExportCountryHistory.HistoryType.DELETE,
        )
        assert delete_history.count() == 1
        assert delete_history[0].country == country
        assert delete_history[0].history_user == new_user
