from datetime import datetime
from operator import attrgetter, itemgetter
from uuid import uuid4

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import CompanyExportCountryHistory
from datahub.company.test.factories import CompanyExportCountryHistoryFactory, CompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.interaction.models import InteractionPermission
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    ExportCountriesInteractionFactory,
    ExportCountriesServiceDeliveryFactory,
)
from datahub.metadata.models import Country
from datahub.search.export_country_history import ExportCountryHistoryApp
from datahub.search.interaction import InteractionSearchApp

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.es_collector_apps.with_args(ExportCountryHistoryApp, InteractionSearchApp),
]

HistoryType = CompanyExportCountryHistory.HistoryType
export_country_history_search_url = reverse('api-v4:search:export-country-history')


class TestSearchExportCountryHistory(APITestMixin):
    """Tests search views."""

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            (
                [],
                status.HTTP_403_FORBIDDEN,
            ),
            (
                ['view_companyexportcountry'],
                status.HTTP_403_FORBIDDEN,
            ),
            (
                [InteractionPermission.view_all],
                status.HTTP_403_FORBIDDEN,
            ),
            (
                ['view_companyexportcountry', InteractionPermission.view_all],
                status.HTTP_200_OK,
            ),
        ),
    )
    @pytest.mark.usefixtures('es')
    def test_permission_checking(self, permission_codenames, expected_status, api_client):
        """Test that the expected status is returned for various user permissions."""
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            export_country_history_search_url,
            data={
                'company': uuid4(),
            },
        )
        assert response.status_code == expected_status

    def test_export_country_history_search_with_empty_request(self, es_with_collector):
        """Should return 400."""
        es_with_collector.flush_and_refresh()
        error_response = 'Request must include either country or company parameters'

        response = self.api_client.post(export_country_history_search_url, data={})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['non_field_errors'][0] == error_response

    def test_export_country_history_response_body(self, es_with_collector):
        """Test the format of an export country history result in the response body."""
        history_object = CompanyExportCountryHistoryFactory(history_type=HistoryType.INSERT)
        es_with_collector.flush_and_refresh()

        response = self.api_client.post(
            export_country_history_search_url,
            data={
                # The view requires a filter
                'company': history_object.company.pk,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        results = response.json()['results']
        assert len(results) == 1
        assert results[0] == {
            'company': {
                'id': str(history_object.company.pk),
                'name': history_object.company.name,
            },
            'country': {
                'id': str(history_object.country.pk),
                'name': history_object.country.name,
            },
            'date': history_object.history_date.isoformat(),
            'history_date': history_object.history_date.isoformat(),
            'history_type': history_object.history_type,
            'history_user': {
                'id': str(history_object.history_user.pk),
                'name': history_object.history_user.name,
            },
            'id': str(history_object.pk),
            'status': history_object.status,
        }

    def test_interaction_response_body(self, es_with_collector):
        """Test the format of an interaction result in the response body."""
        interaction = ExportCountriesInteractionFactory()
        es_with_collector.flush_and_refresh()

        response = self.api_client.post(
            export_country_history_search_url,
            data={
                # The view requires a filter
                'company': interaction.company.pk,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        results = response.json()['results']
        assert len(results) == 1

        result = results[0]
        result['contacts'].sort(key=itemgetter('id'))
        result['dit_participants'].sort(key=lambda participant: participant['adviser']['id'])
        result['export_countries'].sort(key=lambda export_country: export_country['country']['id'])

        assert result == {
            'company': {
                'id': str(interaction.company.pk),
                'name': interaction.company.name,
                'trading_names': interaction.company.trading_names,
            },
            'contacts': [
                {
                    'id': str(contact.pk),
                    'first_name': contact.first_name,
                    'name': contact.name,
                    'last_name': contact.last_name,
                }
                for contact in sorted(interaction.contacts.all(), key=attrgetter('id'))
            ],
            'date': interaction.date.isoformat(),
            'dit_participants': [
                {
                    'adviser': {
                        'id': str(dit_participant.adviser.pk),
                        'first_name': dit_participant.adviser.first_name,
                        'name': dit_participant.adviser.name,
                        'last_name': dit_participant.adviser.last_name,
                    },
                    'team': {
                        'id': str(dit_participant.team.pk),
                        'name': dit_participant.team.name,
                    },
                }
                for dit_participant in interaction.dit_participants.order_by('adviser__pk')
            ],
            'export_countries': [
                {
                    'country': {
                        'id': str(export_country.country.pk),
                        'name': export_country.country.name,
                    },
                    'status': export_country.status,
                }
                for export_country in interaction.export_countries.order_by('country__pk')
            ],
            'id': str(interaction.pk),
            'service': {
                'id': str(interaction.service.pk),
                'name': interaction.service.name,
            },
            'subject': interaction.subject,
        }

    @pytest.mark.parametrize(
        'factory',
        (
            lambda: CompanyExportCountryHistoryFactory(history_type=HistoryType.INSERT),
            lambda: CompanyExportCountryHistoryFactory(history_type=HistoryType.DELETE),
            ExportCountriesInteractionFactory,
            ExportCountriesServiceDeliveryFactory,
        ),
    )
    def test_filter_by_company_returns_matches(self, es_with_collector, factory):
        """Test that filtering by company includes matching objects."""
        obj = factory()
        es_with_collector.flush_and_refresh()

        response = self.api_client.post(
            export_country_history_search_url,
            data={
                'company': obj.company.pk,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['id'] == str(obj.pk)

    def test_filter_by_company_excludes_non_matches(self, es_with_collector):
        """Test that filtering by company excludes non-matching objects."""
        company = CompanyFactory()

        # Updates should be excluded
        CompanyExportCountryHistoryFactory(company=company, history_type=HistoryType.UPDATE)

        # Non-export country interactions should be excluded
        CompanyInteractionFactory(company=company)

        # Unrelated companies should be excluded
        CompanyExportCountryHistoryFactory(history_type=HistoryType.INSERT)
        ExportCountriesInteractionFactory()

        es_with_collector.flush_and_refresh()

        response = self.api_client.post(
            export_country_history_search_url,
            data={
                'company': company.pk,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == 0
        assert response_data['results'] == []

    @pytest.mark.parametrize(
        'factory',
        (
            lambda: CompanyExportCountryHistoryFactory(history_type=HistoryType.INSERT),
            lambda: CompanyExportCountryHistoryFactory(history_type=HistoryType.DELETE),
        ),
    )
    def test_filter_by_country_returns_matching_history_objects(self, es_with_collector, factory):
        """Test that filtering by country includes matching export country history objects."""
        obj = factory()
        es_with_collector.flush_and_refresh()

        response = self.api_client.post(
            export_country_history_search_url,
            data={
                'country': obj.country.pk,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['id'] == str(obj.pk)

    @pytest.mark.parametrize(
        'factory',
        (
            ExportCountriesInteractionFactory,
            ExportCountriesServiceDeliveryFactory,
        ),
    )
    def test_filter_by_country_returns_matching_interactions(self, es_with_collector, factory):
        """Test that filtering by country includes matching interactions."""
        obj = factory()
        es_with_collector.flush_and_refresh()

        response = self.api_client.post(
            export_country_history_search_url,
            data={
                'country': obj.export_countries.first().country.pk,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['id'] == str(obj.pk)

    def test_filter_by_country_excludes_non_matches(self, es_with_collector):
        """Test that filtering by country excludes non-matching objects."""
        countries = list(Country.objects.order_by('?')[:2])
        filter_country = countries[0]
        other_country = countries[1]

        # Updates should be excluded
        CompanyExportCountryHistoryFactory(country=filter_country, history_type=HistoryType.UPDATE)

        # Non-export country interactions should be excluded
        CompanyInteractionFactory()

        # Unrelated countries should be excluded
        CompanyExportCountryHistoryFactory(country=other_country, history_type=HistoryType.INSERT)
        ExportCountriesInteractionFactory(export_countries__country=other_country)

        es_with_collector.flush_and_refresh()

        response = self.api_client.post(
            export_country_history_search_url,
            data={
                'country': filter_country.pk,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == 0
        assert response_data['results'] == []

    @pytest.mark.parametrize(
        'request_args,is_reversed',
        (
            # default sorting
            ({}, True),
            ({'sortby': 'date:asc'}, False),
            ({'sortby': 'date:desc'}, True),
        ),
    )
    def test_sorts_results(self, es_with_collector, request_args, is_reversed):
        """
        Test sorting in various cases.

        Note that a filter is mandatory in this view, hence the test filters by company.
        """
        datetimes = [
            datetime(2001, 1, 22, tzinfo=utc),
            datetime(2002, 2, 23, 1, 2, 3, tzinfo=utc),
            datetime(2003, 3, 24, tzinfo=utc),
            datetime(2004, 4, 25, 1, 2, 3, tzinfo=utc),
        ]
        company = CompanyFactory()

        objects = [
            ExportCountriesInteractionFactory(date=datetimes.pop(0), company=company),
            _make_dated_export_country_history(datetimes.pop(0), company=company),
            ExportCountriesInteractionFactory(date=datetimes.pop(0), company=company),
            _make_dated_export_country_history(datetimes.pop(0), company=company),
        ]

        if is_reversed:
            objects.reverse()

        es_with_collector.flush_and_refresh()

        response = self.api_client.post(
            export_country_history_search_url,
            data={
                'company': company.pk,
                **request_args,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        expected_result_ids = [str(obj.pk) for obj in objects]
        actual_result_ids = [result['id'] for result in response.json()['results']]

        assert actual_result_ids == expected_result_ids


def _make_dated_export_country_history(history_date, **kwargs):
    with freeze_time(history_date):
        return CompanyExportCountryHistoryFactory(history_type=HistoryType.INSERT, **kwargs)
