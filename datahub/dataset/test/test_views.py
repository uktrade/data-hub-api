import pytest
from django.conf import settings
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import (
    ArchivedContactFactory,
    ContactFactory,
    ContactWithOwnAddressFactory,
)
from datahub.core.test_utils import (
    format_date_or_datetime,
    get_attr_or_none,
    HawkAPITestClient,
    join_attr_values,
)
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    CompanyInteractionFactoryWithPolicyFeedback,
    EventServiceDeliveryFactory,
    InvestmentProjectInteractionFactory,
    ServiceDeliveryFactory,
)
from datahub.omis.order.test.factories import (
    OrderCancelledFactory,
    OrderCompleteFactory,
    OrderFactory,
    OrderPaidFactory,
    OrderWithAcceptedQuoteFactory,
    OrderWithCancelledQuoteFactory,
    OrderWithOpenQuoteFactory,
    OrderWithoutAssigneesFactory,
    OrderWithoutLeadAssigneeFactory,
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


@pytest.fixture
def omis_dataset_view_url():
    """Returns OMISDatasetView url"""
    yield reverse('api-v4:dataset:omis-dataset')


@pytest.fixture
def contacts_dataset_view_url():
    """Returns ContactsDatasetView url"""
    yield reverse('api-v4:dataset:contacts-dataset')


@pytest.fixture
def interactions_dataset_view_url():
    """Returns InteractionsDatasetView url"""
    yield reverse('api-v4:dataset:interactions-dataset')


def get_expected_data_from_order(order):
    """Returns expected dictionary based on given order"""
    return {
        'delivery_date': str(order.delivery_date),
        'services': join_attr_values(order.service_types.order_by('name')),
        'status': order.status,
        'reference': order.reference,
        'subtotal_cost': order.subtotal_cost,
        'invoice__subtotal_cost': get_attr_or_none(order, 'invoice.subtotal_cost'),
        'company__name': order.company.name,
        'created_by__dit_team__name': order.created_by.dit_team.name,
        'primary_market__name': order.primary_market.name,
        'created_on': (format_date_or_datetime(order.created_on)
                       if order.created_on else None),
        'cancelled_on': (format_date_or_datetime(order.cancelled_on)
                         if order.cancelled_on else None),
        'cancellation_reason__name': get_attr_or_none(order, 'cancellation_reason.name'),
        'uk_region__name': order.uk_region.name,
        'sector__segment': order.sector.segment,
        'paid_on': (format_date_or_datetime(order.paid_on)
                    if order.paid_on else None),
        'completed_on': (format_date_or_datetime(order.completed_on)
                         if order.completed_on else None),
        'contact__first_name': order.contact.first_name,
        'contact__last_name': order.contact.last_name,
        'contact__telephone_number': order.contact.telephone_number,
        'contact__email': order.contact.email,
        'company__address_1': order.company.address_1,
        'company__address_2': order.company.address_2,
        'company__address_town': order.company.address_town,
        'company__address_county': order.company.address_county,
        'company__address_country__name': order.company.address_country.name,
        'company__address_postcode': order.company.address_postcode,
        'company__registered_address_1': order.company.registered_address_1,
        'company__registered_address_2': order.company.registered_address_2,
        'company__registered_address_town': order.company.registered_address_town,
        'company__registered_address_county': order.company.registered_address_county,
        'company__registered_address_country__name': order.company.registered_address_country.name,
        'company__registered_address_postcode': order.company.registered_address_postcode,
    }


@pytest.mark.django_db
class TestOMISDatasetViewSet:
    """
    Tests for OMISDatasetView
    """

    @pytest.mark.parametrize('method', ('delete', 'patch', 'post', 'put'))
    def test_other_methods_not_allowed(self, data_flow_api_client, method, omis_dataset_view_url):
        """Test that various HTTP methods are not allowed."""
        response = data_flow_api_client.request(method, omis_dataset_view_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_without_scope(self, hawk_api_client, omis_dataset_view_url):
        """Test that making a request without the correct Hawk scope returns an error."""
        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        response = hawk_api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_credentials(self, api_client, omis_dataset_view_url):
        """Test that making a request without credentials returns an error."""
        response = api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'order_factory', (
            OrderFactory,
            OrderCompleteFactory,
            OrderCancelledFactory,
            OrderPaidFactory,
            OrderWithAcceptedQuoteFactory,
            OrderWithCancelledQuoteFactory,
            OrderWithOpenQuoteFactory,
            OrderWithoutAssigneesFactory,
            OrderWithoutLeadAssigneeFactory,
        ))
    def test_success(self, data_flow_api_client, omis_dataset_view_url, order_factory):
        """Test that endpoint returns with expected data for a single order"""
        order = order_factory()
        response = data_flow_api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_order(order)
        assert result == expected_result

    def test_with_multiple_orders(self, data_flow_api_client, omis_dataset_view_url):
        """Test that endpoint returns correct number of record in expected order"""
        with freeze_time('2019-01-01 12:30:00'):
            order_1 = OrderFactory()
        with freeze_time('2019-01-03 12:00:00'):
            order_2 = OrderFactory()
        with freeze_time('2019-01-01 12:00:00'):
            order_3 = OrderFactory()
            order_4 = OrderFactory()

        response = data_flow_api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_order_list = sorted([order_3, order_4],
                                     key=lambda item: item.pk) + [order_1, order_2]
        for index, order in enumerate(expected_order_list):
            assert order.reference == response_results[index]['reference']

    def test_pagination(self, data_flow_api_client, omis_dataset_view_url):
        """Test that when page size higher than threshold response returns with next page url"""
        OrderFactory.create_batch(settings.REST_FRAMEWORK['PAGE_SIZE'] + 1)
        response = data_flow_api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['next'] is not None

    def test_no_data(self, data_flow_api_client, omis_dataset_view_url):
        """Test that without any data available, endpoint completes the request successfully"""
        response = data_flow_api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK


def get_expected_data_from_contact(contact):
    """Returns expected dictionary based on given contact"""
    return {
        'accepts_dit_email_marketing': contact.accepts_dit_email_marketing,
        'address_country__name': get_attr_or_none(contact, 'address_country.name'),
        'address_postcode': contact.address_postcode,
        'company__company_number': get_attr_or_none(contact, 'company.company_number'),
        'company__name': get_attr_or_none(contact, 'company.name'),
        'company__uk_region__name': get_attr_or_none(contact, 'company.uk_region.name'),
        'company_sector': get_attr_or_none(contact, 'company.sector.name'),
        'created_on': format_date_or_datetime(contact.created_on),
        'email': contact.email,
        'email_alternative': contact.email_alternative,
        'job_title': contact.job_title,
        'name': contact.name,
        'notes': contact.notes,
        'telephone_alternative': contact.telephone_alternative,
        'telephone_number': contact.telephone_number,
    }


@pytest.mark.django_db
class TestContactsDatasetViewSet:
    """
    Tests for ContactsDatasetView
    """

    @pytest.mark.parametrize('method', ('delete', 'patch', 'post', 'put'))
    def test_other_methods_not_allowed(
        self,
        data_flow_api_client,
        method,
        contacts_dataset_view_url,
    ):
        """Test that various HTTP methods are not allowed."""
        response = data_flow_api_client.request(method, contacts_dataset_view_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_without_scope(self, hawk_api_client, contacts_dataset_view_url):
        """Test that making a request without the correct Hawk scope returns an error."""
        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        response = hawk_api_client.get(contacts_dataset_view_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_credentials(self, api_client, contacts_dataset_view_url):
        """Test that making a request without credentials returns an error."""
        response = api_client.get(contacts_dataset_view_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'contact_factory', (
            ArchivedContactFactory,
            ContactFactory,
            ContactWithOwnAddressFactory,
        ))
    def test_success(self, data_flow_api_client, contacts_dataset_view_url, contact_factory):
        """Test that endpoint returns with expected data for a single order"""
        contact = contact_factory()
        response = data_flow_api_client.get(contacts_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_contact(contact)
        assert result == expected_result

    def test_with_multiple_contacts(self, data_flow_api_client, contacts_dataset_view_url):
        """Test that endpoint returns correct number of record in expected contact"""
        with freeze_time('2019-01-01 12:30:00'):
            contact_1 = ContactFactory()
        with freeze_time('2019-01-03 12:00:00'):
            contact_2 = ContactFactory()
        with freeze_time('2019-01-01 12:00:00'):
            contact_3 = ContactFactory()
            contact_4 = ContactFactory()

        response = data_flow_api_client.get(contacts_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_contact_list = sorted([contact_3, contact_4],
                                       key=lambda item: item.pk) + [contact_1, contact_2]
        for index, contact in enumerate(expected_contact_list):
            assert contact.email == response_results[index]['email']

    def test_pagination(self, data_flow_api_client, contacts_dataset_view_url):
        """Test that when page size higher than threshold response returns with next page url"""
        OrderFactory.create_batch(settings.REST_FRAMEWORK['PAGE_SIZE'] + 1)
        response = data_flow_api_client.get(contacts_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['next'] is not None

    def test_no_data(self, data_flow_api_client, contacts_dataset_view_url):
        """Test that without any data available, endpoint completes the request successfully"""
        response = data_flow_api_client.get(contacts_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK


def get_expected_data_from_interaction(interaction):
    """Returns expected API response dictionary for the given interaction"""
    participant = interaction.dit_participants.order_by('pk').last()
    contact = interaction.contacts.all().order_by('pk').last()
    return {
        'date': format_date_or_datetime(interaction.date),
        'kind': interaction.kind,
        'company__name': interaction.company.name,
        'company__company_number': interaction.company.company_number,
        'company__id': str(interaction.company.id),
        'investment_project__cdms_project_code': get_attr_or_none(
            interaction,
            'investment_project.cdms_project_code',
        ),
        'company__address_postcode': interaction.company.address_postcode,
        'company__address_1': interaction.company.address_1,
        'company__address_2': interaction.company.address_2,
        'company__address_town': interaction.company.address_town,
        'company__address_country__name': interaction.company.address_country.name,
        'company__website': interaction.company.website,
        'company__employee_range__name': interaction.company.employee_range.name,
        'company__turnover_range__name': interaction.company.turnover_range.name,
        'company__uk_region__name': interaction.company.uk_region.name,
        'subject': interaction.subject,
        'notes': interaction.notes,
        'net_company_receipt': (
            float(interaction.net_company_receipt)
            if interaction.net_company_receipt is not None
            else None
        ),
        'grant_amount_offered': (
            float(interaction.grant_amount_offered)
            if interaction.grant_amount_offered is not None
            else None
        ),
        'service_delivery_status__name': get_attr_or_none(
            interaction,
            'service_delivery_status.name',
        ),
        'event__name': get_attr_or_none(interaction, 'event.name'),
        'event__event_type__name': get_attr_or_none(
            interaction, 'event.event_type.name',
        ),
        'event__start_date': (
            format_date_or_datetime(interaction.event.start_date)
            if interaction.event is not None
            else None
        ),
        'event__address_town': get_attr_or_none(interaction, 'event.address_town'),
        'event__address_country__name': get_attr_or_none(
            interaction,
            'event.address_country.name',
        ),
        'event__uk_region__name': get_attr_or_none(interaction, 'event.uk_region.name'),
        'created_on': format_date_or_datetime(interaction.created_on),
        'communication_channel__name': get_attr_or_none(
            interaction,
            'communication_channel.name',
        ),
        'sector': get_attr_or_none(interaction, 'company.sector.name'),
        'interaction_link': interaction.get_absolute_url(),
        'adviser_name': get_attr_or_none(participant, 'adviser.name'),
        'adviser_phone': get_attr_or_none(participant, 'adviser.telephone_number'),
        'adviser_email': get_attr_or_none(participant, 'adviser.email'),
        'adviser_team': get_attr_or_none(participant, 'adviser.dit_team.name'),
        'service_delivery': get_attr_or_none(interaction, 'service.name'),
        'event_service': get_attr_or_none(interaction, 'event.service.name'),
        'contact_name': contact.name,
        'contact_telephone_number': contact.telephone_number,
        'contact_email': contact.email,
        'contact_address_postcode': contact.address_postcode,
        'contact_address_1': contact.address_1,
        'contact_address_2': contact.address_2,
        'contact_address_town': contact.address_town,
        'contact_address_country': get_attr_or_none(
            contact,
            'address_country.name',
        ),
    }


@pytest.mark.django_db
class TestInteractionsDatasetView:
    """
    Tests for InteractionsDatasetView
    """

    @pytest.mark.parametrize('method', ('delete', 'patch', 'post', 'put'))
    def test_other_methods_not_allowed(
        self,
        data_flow_api_client,
        method,
        interactions_dataset_view_url,
    ):
        """Test that various HTTP methods are not allowed."""
        response = data_flow_api_client.request(method, interactions_dataset_view_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_without_scope(self, hawk_api_client, interactions_dataset_view_url):
        """Test that making a request without the correct Hawk scope returns an error."""
        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        response = hawk_api_client.get(interactions_dataset_view_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_credentials(self, api_client, interactions_dataset_view_url):
        """Test that making a request without credentials returns an error."""
        response = api_client.get(interactions_dataset_view_url)
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
    def test_success(
            self,
            data_flow_api_client,
            interactions_dataset_view_url,
            interaction_factory,
    ):
        """Test that endpoint returns with expected data for a single interaction"""
        interaction = interaction_factory()
        response = data_flow_api_client.get(interactions_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_interaction(interaction)
        assert result == expected_result

    def test_with_multiple_interactions(self, data_flow_api_client, interactions_dataset_view_url):
        """Test that the correct number of records are returned in the right order"""
        with freeze_time('2019-01-01 12:30:00'):
            interaction1 = CompanyInteractionFactory()
        with freeze_time('2019-01-03 12:00:00'):
            interaction2 = CompanyInteractionFactory()
        with freeze_time('2019-01-01 12:00:00'):
            interaction3 = CompanyInteractionFactory()
            interaction4 = CompanyInteractionFactory()

        response = data_flow_api_client.get(interactions_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_list = sorted(
            [interaction3, interaction4],
            key=lambda item: item.pk,
        ) + [interaction1, interaction2]
        for index, interaction in enumerate(expected_list):
            assert interaction.get_absolute_url() == response_results[index]['interaction_link']

    def test_pagination(self, data_flow_api_client, interactions_dataset_view_url):
        """Test that the next page url is populated correctly"""
        CompanyInteractionFactory.create_batch(settings.REST_FRAMEWORK['PAGE_SIZE'] + 1)
        response = data_flow_api_client.get(interactions_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['next'] is not None

    def test_no_data(self, data_flow_api_client, interactions_dataset_view_url):
        """Test that an empty dataset is returned successfully"""
        response = data_flow_api_client.get(interactions_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
