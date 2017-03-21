import pytest
from django.test import TestCase

from datahub.interaction.test import factories
from datahub.v2.repos.service_deliveries import ServiceDeliveryDatabaseRepo

pytestmark = pytest.mark.django_db


class ServiceDeliveriesRepoTestCase(TestCase):

    def test_model_to_json_api(self):
        service_delivery = factories.ServiceDeliveryFactory()
        result = ServiceDeliveryDatabaseRepo().get(service_delivery.pk)
        print(result)
        assert result['relationships']
        assert result['relationships']['company']['data']['type'] == 'Company'
        assert result['attributes']['date'] == service_delivery.date.isoformat()
