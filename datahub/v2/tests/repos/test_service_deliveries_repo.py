import uuid

import pytest
from django.utils.timezone import now
from freezegun import freeze_time

from datahub.core import constants
from datahub.core.test_utils import get_test_user
from datahub.interaction.test import factories
from datahub.v2.exceptions import DoesNotExistException
from datahub.v2.repos.service_deliveries import ServiceDeliveryDatabaseRepo
from datahub.v2.repos.utils import RepoResponse

pytestmark = pytest.mark.django_db


DUMMY_CONFIG = config = {'url_builder': lambda kwargs: None}


class TestServiceDeliveriesRepo:
    """Service delivery repo test case."""

    def test_get(self):
        """Test get service delivery."""
        service_offer = factories.ServiceOfferFactory()
        service_delivery = factories.LegacyServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team
        )
        result = ServiceDeliveryDatabaseRepo(config=DUMMY_CONFIG).get(service_delivery.pk)
        data = result.data
        assert isinstance(result, RepoResponse)
        expected_relationships = {
            'contact': {'data': {'id': str(service_delivery.contact.pk), 'type': 'Contact'}},
            'company': {'data': {'id': str(service_delivery.company.pk), 'type': 'Company'}},
            'service': {'data': {'id': str(service_delivery.service.pk), 'type': 'Service'}},
            'dit_team': {'data': {'id': str(service_delivery.dit_team.pk), 'type': 'Team'}},
            'uk_region': {'data': {'id': str(service_delivery.uk_region.pk), 'type': 'UKRegion'}},
            'status': {
                'data': {'id': str(service_delivery.status.pk), 'type': 'ServiceDeliveryStatus'}
            },
            'dit_adviser': {
                'data': {'id': str(service_delivery.dit_adviser.pk), 'type': 'Adviser'}
            }
        }
        assert data['relationships'] == expected_relationships
        assert data['relationships']['company']['data']['type'] == 'Company'
        assert data['attributes']['date'] == service_delivery.date.isoformat()
        assert data['type'] == 'ServiceDelivery'
        assert data['id'] == str(service_delivery.pk)

    def test_get_does_not_exist(self):
        """Test SD does not exist."""
        with pytest.raises(DoesNotExistException):
            ServiceDeliveryDatabaseRepo(config=DUMMY_CONFIG).get(uuid.uuid4())

    @freeze_time('2017-04-01 20:49:40.566277+00:00')
    def test_insert(self):
        """Test add service delivery."""
        service_offer = factories.ServiceOfferFactory()
        user = get_test_user()
        company = factories.CompanyFactory()
        contact = factories.ContactFactory()
        offered_id = constants.ServiceDeliveryStatus.offered.value.id
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
                        'id': offered_id
                    }
                },
                'company': {
                    'data': {
                        'type': 'Company',
                        'id': str(company.pk)
                    }
                },
                'contact': {
                    'data': {
                        'type': 'Contact',
                        'id': str(contact.pk)
                    }
                },
                'service': {
                    'data': {
                        'type': 'Service',
                        'id': str(service_offer.service.pk)
                    }
                },
                'dit_team': {
                    'data': {
                        'type': 'Team',
                        'id': str(service_offer.dit_team.pk)
                    }
                },
                'dit_adviser': {
                    'data': {
                        'type': 'Adviser',
                        'id': str(user.pk)
                    }
                },
            }
        }
        result = ServiceDeliveryDatabaseRepo(config=DUMMY_CONFIG).upsert(data=data)
        data = result.data
        assert isinstance(result, RepoResponse)
        expected_attributes = {
            'date': '2017-04-01T20:49:40.566277+00:00',
            'subject': 'whatever',
            'feedback': None,
            'notes': 'hello'
        }
        assert data['attributes'] == expected_attributes
        assert data['type'] == 'ServiceDelivery'
        expected_relationships = {
            'dit_adviser': {'data': {'type': 'Adviser', 'id': str(user.pk)}},
            'status': {'data': {
                'type': 'ServiceDeliveryStatus', 'id': offered_id}
            },
            'contact': {'data': {'type': 'Contact', 'id': str(contact.pk)}},
            'dit_team': {'data': {'type': 'Team', 'id': str(service_offer.dit_team.pk)}},
            'service': {'data': {'type': 'Service', 'id': str(service_offer.service.pk)}},
            'company': {'data': {'type': 'Company', 'id': str(company.pk)}},
            'service_offer': {'data': {'type': 'ServiceOffer', 'id': str(service_offer.pk)}}
        }
        assert data['relationships'] == expected_relationships

    def test_update(self):
        """Test update existing service delivery."""
        service_offer = factories.ServiceOfferFactory()
        service_delivery = factories.LegacyServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
            subject='foo'
        )
        contact = factories.ContactFactory()
        data = {
            'type': 'ServiceDelivery',
            'id': str(service_delivery.pk),
            'attributes': {
                'subject': 'whatever',
            },
            'relationships': {
                'contact': {
                    'data': {
                        'type': 'Contact',
                        'id': str(contact.pk)
                    }
                }
            }
        }
        result = ServiceDeliveryDatabaseRepo(config=DUMMY_CONFIG).upsert(data=data)
        data = result.data
        assert isinstance(result, RepoResponse)
        assert data['attributes']['subject'] == 'whatever'
        assert data['relationships']['contact']['data']['id'] == str(contact.pk)

    def test_filter_with_pagination(self):
        """Test filter with pagination."""
        service_offer = factories.ServiceOfferFactory()
        service_deliveries = [
            factories.LegacyServiceDeliveryFactory(
                service=service_offer.service,
                dit_team=service_offer.dit_team)
            for i in range(6)]
        result = ServiceDeliveryDatabaseRepo(config=DUMMY_CONFIG).filter(offset=2, limit=3)
        data = result.data
        assert isinstance(result, RepoResponse)
        assert data[0]['id'] == str(service_deliveries[2].id)
        assert data[2]['id'] == str(service_deliveries[4].id)

    def test_filter_by_company_id(self):
        """Test filter by company id."""
        service_offer = factories.ServiceOfferFactory()
        company = factories.CompanyFactory()
        factories.LegacyServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
        )
        service_delivery = factories.LegacyServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
            company=company
        )
        result = ServiceDeliveryDatabaseRepo(config=DUMMY_CONFIG).filter(
            company_id=str(company.pk)
        )
        data = result.data
        assert isinstance(result, RepoResponse)
        assert len(data) == 1
        assert data[0]['id'] == str(service_delivery.pk)

    def test_filter_by_contact_id(self):
        """Test filter by contact id."""
        service_offer = factories.ServiceOfferFactory()
        contact = factories.ContactFactory()
        factories.LegacyServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
        )
        service_delivery = factories.LegacyServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
            contact=contact
        )
        result = ServiceDeliveryDatabaseRepo(config=DUMMY_CONFIG).filter(
            contact_id=str(contact.pk)
        )
        data = result.data
        assert isinstance(result, RepoResponse)
        assert len(data) == 1
        assert data[0]['id'] == str(service_delivery.pk)

    def test_filter_by_contact_and_company_ids(self):
        """Test filter by contact and company ids."""
        service_offer = factories.ServiceOfferFactory()
        contact = factories.ContactFactory()
        company = factories.CompanyFactory()
        factories.LegacyServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
        )
        service_delivery = factories.LegacyServiceDeliveryFactory(
            service=service_offer.service,
            dit_team=service_offer.dit_team,
            contact=contact,
            company=company
        )
        result = ServiceDeliveryDatabaseRepo(config=DUMMY_CONFIG).filter(
            contact_id=str(contact.pk),
            company_id=str(company.pk)
        )
        data = result.data
        assert isinstance(result, RepoResponse)
        assert len(data) == 1
        assert data[0]['id'] == str(service_delivery.pk)
