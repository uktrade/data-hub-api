import pytest
from django.conf import settings
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from datahub.core.test_utils import format_date_or_datetime, get_attr_or_none, HawkAPITestClient
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    CompanyInteractionFactoryWithPolicyFeedback,
    EventServiceDeliveryFactory,
    InvestmentProjectInteractionFactory,
    ServiceDeliveryFactory,
)


@pytest.fixture
def hawk_api_client():
    """Hawk API client fixture."""
    yield HawkAPITestClient()


@pytest.fixture
def data_flow_api_client(hawk_api_client):
    """Hawk API client fixture configured to use credentials with the data_flow_api scope."""
    hawk_api_client.set_credentials(
        'data-flow-api-id',
        'data-flow-api-key',
    )
    yield hawk_api_client


def get_expected_data_from_interaction(interaction):
    """Returns expected API response dictionary for an interaction"""
    return {
        'adviser_ids': [
            str(x.adviser_id)
            for x in interaction.dit_participants.all().order_by('pk')
        ],
        'communication_channel__name': get_attr_or_none(
            interaction,
            'communication_channel.name',
        ),
        'company_id': str(interaction.company.id),
        'contact_ids': [str(x.id) for x in interaction.contacts.all().order_by('pk')],
        'created_on': format_date_or_datetime(interaction.created_on),
        'date': format_date_or_datetime(interaction.date),
        'event_id': (
            str(interaction.event_id)
            if interaction.event_id is not None
            else None
        ),
        'grant_amount_offered': (
            float(interaction.grant_amount_offered)
            if interaction.grant_amount_offered is not None
            else None
        ),
        'interaction_link': interaction.get_absolute_url(),
        'investment_project_id': (
            str(interaction.investment_project_id)
            if interaction.investment_project is not None
            else None
        ),
        'kind': interaction.kind,
        'net_company_receipt': (
            float(interaction.net_company_receipt)
            if interaction.net_company_receipt is not None
            else None
        ),
        'notes': interaction.notes,
        'sector': get_attr_or_none(interaction, 'company.sector.name'),
        'service_delivery_status__name': get_attr_or_none(
            interaction,
            'service_delivery_status.name',
        ),
        'service_delivery': get_attr_or_none(interaction, 'service.name'),
        'subject': interaction.subject,
    }


@pytest.mark.django_db
class TestInteractionsDatasetViewSet:
    """
    Tests for InteractionsDatasetView
    """

    view_url = reverse('api-v4:dataset:interactions-dataset')

    @pytest.mark.parametrize('method', ('delete', 'patch', 'post', 'put'))
    def test_other_methods_not_allowed(
        self,
        data_flow_api_client,
        method,
    ):
        """Test that various HTTP methods are not allowed."""
        response = data_flow_api_client.request(method, self.view_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_without_scope(self, hawk_api_client):
        """Test that making a request without the correct Hawk scope returns an error."""
        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        response = hawk_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_credentials(self, api_client):
        """Test that making a request without credentials returns an error."""
        response = api_client.get(self.view_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_without_whitelisted_ip(self, data_flow_api_client):
        """Test that making a request without the whitelisted IP returns an error."""
        data_flow_api_client.set_http_x_forwarded_for('1.1.1.1')
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'interaction_factory', (
            CompanyInteractionFactory,
            CompanyInteractionFactoryWithPolicyFeedback,
            EventServiceDeliveryFactory,
            InvestmentProjectInteractionFactory,
            ServiceDeliveryFactory,
        ),
    )
    def test_success(self, data_flow_api_client, interaction_factory):
        """Test that endpoint returns with expected data for a single interaction"""
        interaction = interaction_factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_interaction(interaction)
        assert result == expected_result

    def test_with_multiple_interactions(self, data_flow_api_client):
        """Test that the correct number of records are returned in the right order"""
        with freeze_time('2019-01-01 12:30:00'):
            interaction1 = CompanyInteractionFactory()
        with freeze_time('2019-01-03 12:00:00'):
            interaction2 = CompanyInteractionFactory()
        with freeze_time('2019-01-01 12:00:00'):
            interaction3 = CompanyInteractionFactory()
            interaction4 = CompanyInteractionFactory()

        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_list = sorted(
            [interaction3, interaction4],
            key=lambda item: item.pk,
        ) + [interaction1, interaction2]
        for index, interaction in enumerate(expected_list):
            assert interaction.get_absolute_url() == response_results[index]['interaction_link']

    def test_pagination(self, data_flow_api_client):
        """Test that the next page url is populated correctly"""
        CompanyInteractionFactory.create_batch(settings.REST_FRAMEWORK['PAGE_SIZE'] + 1)
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['next'] is not None

    def test_no_data(self, data_flow_api_client):
        """Test that an empty dataset is returned successfully"""
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
