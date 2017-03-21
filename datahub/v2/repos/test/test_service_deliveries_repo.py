import uuid

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from datahub.interaction.test import factories
from datahub.v2.repos.service_deliveries import ServiceDeliveryDatabaseRepo

pytestmark = pytest.mark.django_db


class ServiceDeliveriesRepoTestCase(TestCase):

    def test_get(self):
        service_delivery = factories.ServiceDeliveryFactory()
        result = ServiceDeliveryDatabaseRepo().get(service_delivery.pk)
        assert result['relationships']
        assert result['relationships']['company']['data']['type'] == 'Company'
        assert result['attributes']['date'] == service_delivery.date.isoformat()

    def test_get_does_not_exist(self):
        with pytest.raises(ObjectDoesNotExist) as e:
            ServiceDeliveryDatabaseRepo().get(uuid.uuid4())
