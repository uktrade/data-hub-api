from datetime import datetime, timezone
from unittest import mock
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.db import DatabaseError
from reversion.models import Version

from datahub.company.models import Company, Contact
from datahub.company.test.factories import (
    CompanyFactory,
    ContactFactory,
)
from datahub.interaction.models import Interaction
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.models import InvestmentDeliveryPartner, InvestmentProject
from datahub.investment.project.test.factories import InvestmentProjectFactory, InvestmentDeliveryPartnerFactory


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
    """Simple replacement as fixtures can't be used in @pytest.mark.parametrize
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
        from pprint import pprint
        delivery_partners = replace_with_fixtures(
            delivery_partners, lep, dpi)
        expected_partners = replace_with_fixtures(
            expected_partners, lep, dpi)
        pprint(actual_land_date)
        pprint(delivery_partners)
        pprint(expected_partners)

        investment_project = InvestmentProjectFactory(
            actual_land_date=actual_land_date, delivery_partners=delivery_partners)

        call_command('update_investment_delivery_partners')

        pprint(investment_project.__dict__)
        stored_investment_project = InvestmentProject.objects.get(
            pk=investment_project.id)
        assert set([str(value.id) for value in stored_investment_project.delivery_partners.all(
        )]) == set([str(expected_partner.id) for expected_partner in expected_partners])

    def test_idp_added(self, test_base_stova_attendee, simulate, caplog):
        """Test interactions created by Stova Attendees are removed and interactions not created by
        stova are not removed.
        """
        s3_processor_mock = mock.Mock()
        task = StovaAttendeeIngestionTask('dummy-prefix', s3_processor_mock)
        data = test_base_stova_attendee
        task._process_record(data)
        data['id'] = 9876
        task._process_record(data)
        data['id'] = 8907
        data['company_name'] = 'a new company'
        task._process_record(data)
        CompanyInteractionFactory.create_batch(5)

        assert Interaction.objects.count() == 8

        caplog.set_level('INFO')
        call_command('remove_stova_relations', simulate=simulate)

        log_text = caplog.text
        assert 'There were 3 interactions deleted out of 3' in log_text
        assert Interaction.objects.count() == 5
