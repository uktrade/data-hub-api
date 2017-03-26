import uuid

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.utils.timezone import now

from datahub.core import constants
from datahub.core.test_utils import get_test_user
from datahub.interaction.models import ServiceDelivery
from datahub.interaction.test import factories
from datahub.v2.repos.service_deliveries import ServiceDeliveryDatabaseRepo

pytestmark = pytest.mark.django_db


class ServiceDeliveriesRepoTestCase(TestCase):
    """Service delivery repo test case."""

    def test_get(self):
        """Test get service delivery."""
        service_offer = factories.ServiceOfferFactory()
        service_delivery = factories.ServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team
        )
        result = ServiceDeliveryDatabaseRepo().get(service_delivery.pk)
        assert result['relationships']
        assert result['relationships']['company']['data']['type'] == 'Company'
        assert result['attributes']['date'] == service_delivery.date.isoformat()
        assert result['type'] == 'ServiceDelivery'

    def test_get_does_not_exist(self):
        """Test SD does not exist."""
        with pytest.raises(ObjectDoesNotExist):
            ServiceDeliveryDatabaseRepo().get(uuid.uuid4())

    def test_insert(self):
        """Test add service delivery."""
        service_offer = factories.ServiceOfferFactory()
        user = get_test_user()
        data = {
            'type': 'ServiceDelivery',
            'attributes': {
                'subject': 'whatever',
                'date': now().isoformat(),
                'notes': 'hello',
            },
            'relationships': {
                'status': {
                    'data': {
                        'type': 'ServiceDeliveryStatus',
                        'id': constants.ServiceDeliveryStatus.offered.value.id
                    }
                },
                'company': {
                    'data': {
                        'type': 'Company',
                        'id': factories.CompanyFactory().pk
                    }
                },
                'contact': {
                    'data': {
                        'type': 'Contact',
                        'id': factories.ContactFactory().pk
                    }
                },
                'service': {
                    'data': {
                        'type': 'Service',
                        'id': service_offer.service.pk
                    }
                },
                'dit_team': {
                    'data': {
                        'type': 'Team',
                        'id': service_offer.dit_team.pk
                    }
                },
                'dit_advisor': {
                    'data': {
                        'type': 'Advisor',
                        'id': user.pk
                    }
                }
            }
        }
        result = ServiceDeliveryDatabaseRepo().upsert(data=data)
        assert isinstance(result, ServiceDelivery)
        assert result.dit_advisor.pk == user.pk
        assert result.service_id == service_offer.service.pk
        assert result.dit_team_id == service_offer.dit_team.pk

    def test_update(self):
        """Test update existing service delivery."""
        service_offer = factories.ServiceOfferFactory()
        service_delivery = factories.ServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
            subject='foo'
        )
        contact = factories.ContactFactory()
        data = {
            'type': 'ServiceDelivery',
            'attributes': {
                'id': str(service_delivery.pk),
                'subject': 'whatever',
            },
            'relationships': {
                'contact': {
                    'data': {
                        'type': 'Contact',
                        'id': contact.pk
                    }
                }
            }
        }
        result = ServiceDeliveryDatabaseRepo().upsert(data=data)
        assert isinstance(result, ServiceDelivery)
        assert result.subject == 'whatever'
        assert result.contact_id == contact.pk

    def test_filter_with_pagination(self):
        """Test filter with pagination."""
        service_offer = factories.ServiceOfferFactory()
        service_deliveries = [
            factories.ServiceDeliveryFactory(
                service=service_offer.service,
                dit_team=service_offer.dit_team)
            for i in range(6)]
        result = ServiceDeliveryDatabaseRepo().filter(offset=2, limit=3)
        assert result[0]['attributes']['id'] == str(service_deliveries[2].id)
        assert result[2]['attributes']['id'] == str(service_deliveries[4].id)

    def test_filter_by_company_id(self):
        """Test filter by company id."""
        service_offer = factories.ServiceOfferFactory()
        company = factories.CompanyFactory()
        factories.ServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
        )
        service_delivery = factories.ServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
            company=company
        )
        result = ServiceDeliveryDatabaseRepo().filter(company_id=str(company.pk))
        assert len(result) == 1
        assert result[0]['attributes']['id'] == str(service_delivery.pk)

    def test_filter_by_contact_id(self):
        """Test filter by contact id."""
        service_offer = factories.ServiceOfferFactory()
        contact = factories.ContactFactory()
        factories.ServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
        )
        service_delivery = factories.ServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
            contact=contact
        )
        result = ServiceDeliveryDatabaseRepo().filter(contact_id=str(contact.pk))
        assert len(result) == 1
        assert result[0]['attributes']['id'] == str(service_delivery.pk)

    def test_filter_by_contact_and_company_ids(self):
        """Test filter by contact and company ids."""
        service_offer = factories.ServiceOfferFactory()
        contact = factories.ContactFactory()
        company = factories.CompanyFactory()
        factories.ServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
        )
        service_delivery = factories.ServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
            contact=contact,
            company=company
        )
        result = ServiceDeliveryDatabaseRepo().filter(
            contact_id=str(contact.pk),
            company_id=str(company.pk)
        )
        assert len(result) == 1
        assert result[0]['attributes']['id'] == str(service_delivery.pk)
