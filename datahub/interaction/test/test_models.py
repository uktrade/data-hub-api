import pytest
from django.utils.timezone import now

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.test_utils import get_test_user
from datahub.metadata.models import Service, ServiceDeliveryStatus, Team
from ..models import ServiceDelivery, ServiceOffer


pytestmark = pytest.mark.django_db


def test_service_offer_created_when_service_delivery_created():
    """A service delivery is created and a matching service offer exists."""
    status = ServiceDeliveryStatus.objects.first()
    team = Team.objects.first()
    service = Service.objects.first()
    service_delivery = ServiceDelivery(
        date=now(),
        company=CompanyFactory(),
        contact=ContactFactory(),
        subject='bla',
        dit_advisor=get_test_user(),
        notes='bla',
        status=status,
        dit_team=team,
        service=service
    )
    service_delivery.save()

    assert service_delivery.service_offer.dit_team == service_delivery.dit_team
    assert service_delivery.service_offer.service == service_delivery.service


def test_service_offer_selected_when_service_delivery_created():
    """A service delivery is created and a matching service offer doesn't exist."""
    status = ServiceDeliveryStatus.objects.first()
    team = Team.objects.first()
    service = Service.objects.first()
    service_offer = ServiceOffer(
        dit_team=team,
        service=service
    )
    service_offer.save()
    service_delivery = ServiceDelivery(
        date=now(),
        company=CompanyFactory(),
        contact=ContactFactory(),
        subject='bla',
        dit_advisor=get_test_user(),
        notes='bla',
        status=status,
        dit_team=team,
        service=service
    )
    service_delivery.save()

    assert service_delivery.service_offer == service_offer
