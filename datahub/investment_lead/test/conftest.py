import pytest

from datahub.core import constants
from datahub.core.test_utils import create_test_user
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.test.factories import (
    eyb_lead_triage_record_faker,
    eyb_lead_user_record_faker,
    EYBLeadFactory,
)
from datahub.metadata.models import (
    Country,
    Sector,
    UKRegion,
)


@pytest.fixture
def test_user_with_view_permissions():
    return create_test_user(permission_codenames=['view_eyblead'])


@pytest.fixture
def eyb_lead_triage_data():
    return eyb_lead_triage_record_faker()


@pytest.fixture
def eyb_lead_user_data():
    return eyb_lead_user_record_faker()


@pytest.fixture
def eyb_lead_factory_overrides():
    mining_sector = Sector.objects.get(
        pk=constants.Sector.mining_mining_vehicles_transport_equipment.value.id,
    )
    wales_region = UKRegion.objects.get(
        pk=constants.UKRegion.wales.value.id,
    )
    canada_country = Country.objects.get(
        pk=constants.Country.canada.value.id,
    )
    overrides = {
        'sector': mining_sector,
        'proposed_investment_region': wales_region,
        'address_country': canada_country,
    }
    return overrides


@pytest.fixture
def eyb_lead_instance_from_db(eyb_lead_factory_overrides):
    eyb_lead_factory = EYBLeadFactory(**eyb_lead_factory_overrides)
    return EYBLead.objects.get(pk=eyb_lead_factory.pk)
