from datetime import datetime, timezone

import pytest
from django.core.management import call_command

from datahub.investment.project.models import InvestmentDeliveryPartner, InvestmentProject
from datahub.investment.project.test.factories import (
    InvestmentDeliveryPartnerFactory,
    InvestmentProjectFactory,
)


@pytest.fixture
def lep():
    lep_id = 'e96192bb-09f1-e511-8ffa-e4115bead28a'
    return InvestmentDeliveryPartner.objects.get(pk=lep_id)
    return InvestmentDeliveryPartnerFactory(id=lep_id)


@pytest.fixture
def dpi():
    dpi_id = '4d2d0351-ffaa-4a0d-986a-f13be4ec2198'
    return InvestmentDeliveryPartnerFactory(id=dpi_id)


def replace_with_fixtures(source, lep, dpi):
    """Simple replacement as fixtures can't be used in @pytest.mark.parametrize.
    """
    result = []
    for value in source:
        if value == 'lep':
            result.append(lep)
        if value == 'dpi':
            result.append(dpi)
    return result


class TestUpdateInvestmentDeliveryPartnersCommand:
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        ('actual_land_date', 'delivery_partners', 'expected_partners'),
        [
            # Without actual land date
            (None, ['lep'], ['lep']),
            # Before 1st April 2024
            (datetime(2024, 3, 1, tzinfo=timezone.utc), ['lep'], ['lep']),
            # On 1st April 2024
            (datetime(
                2024, 4, 1, tzinfo=timezone.utc), ['lep'], ['dpi']),
            # After 1st April 2024
            (datetime(
                2025, 4, 1, tzinfo=timezone.utc), ['lep'], ['dpi']),
        ],
    )
    def test_actual_land_date(self, caplog, lep, dpi, actual_land_date, delivery_partners, expected_partners):
        delivery_partners = replace_with_fixtures(
            delivery_partners, lep, dpi)
        expected_partners = replace_with_fixtures(
            expected_partners, lep, dpi)

        investment_project = InvestmentProjectFactory(
            actual_land_date=actual_land_date, delivery_partners=delivery_partners)

        call_command('update_investment_delivery_partners')

        stored_investment_project = InvestmentProject.objects.get(
            pk=investment_project.id)
        assert set([str(value.id) for value in stored_investment_project.delivery_partners.all(
        )]) == set([str(expected_partner.id) for expected_partner in expected_partners])
