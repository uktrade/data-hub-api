from datetime import datetime, timezone
from typing import NoReturn

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


@pytest.fixture
def idp():
    idp_id = '4d2d0351-ffaa-4a0d-986a-f13be4ec2198'
    return InvestmentDeliveryPartnerFactory(id=idp_id)


def replace_with_fixtures(source, lep, idp):
    """Simple replacement as fixtures can't be used in @pytest.mark.parametrize."""
    result = []
    for value in source:
        match value:
            case 'lep':
                result.append(lep)
            case 'idp':
                result.append(idp)
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
            (datetime(2024, 4, 1, tzinfo=timezone.utc), ['lep'], ['idp']),
            # After 1st April 2024
            (datetime(2025, 4, 1, tzinfo=timezone.utc), ['lep'], ['idp']),
        ],
    )
    def test_actual_land_date(
        self,
        caplog: pytest.LogCaptureFixture,
        lep: InvestmentDeliveryPartner,
        idp: NoReturn,
        actual_land_date,
        delivery_partners,
        expected_partners,
    ):
        caplog.set_level('INFO')
        delivery_partners = replace_with_fixtures(delivery_partners, lep, idp)
        expected_partners = replace_with_fixtures(expected_partners, lep, idp)

        investment_project = InvestmentProjectFactory(
            actual_land_date=actual_land_date,
            delivery_partners=delivery_partners,
        )

        call_command('update_investment_delivery_partners', delete=True)

        stored_investment_project = InvestmentProject.objects.get(pk=investment_project.id)
        assert set(
            [str(value.id) for value in stored_investment_project.delivery_partners.all()],
        ) == set([str(expected_partner.id) for expected_partner in expected_partners])

    @pytest.mark.django_db
    def test_multiple_delivery_partners(
        self,
        caplog: pytest.LogCaptureFixture,
        lep: InvestmentDeliveryPartner,
        idp: NoReturn,
    ):
        """Test Investment Project with multiple delivery partners."""
        caplog.set_level('INFO')

        leps = [
            lep,
            InvestmentDeliveryPartner.objects.get(pk='9abd575e-0af1-e511-8ffa-e4115bead28a'),
            InvestmentDeliveryPartner.objects.get(pk='87b87bf6-9f1a-e511-8e8f-441ea13961e2'),
        ]

        idps = [
            idp,
            InvestmentDeliveryPartnerFactory(id='182e76ca-868d-4ca4-a336-17a26719f786'),
            InvestmentDeliveryPartnerFactory(id='dedd7553-63fe-41cc-874f-740d4cec8f97'),
        ]

        investment_project = InvestmentProjectFactory(
            actual_land_date=datetime(2025, 4, 1, tzinfo=timezone.utc),
            delivery_partners=leps,
        )

        call_command('update_investment_delivery_partners', simulate=False, delete=True)

        stored_investment_project = InvestmentProject.objects.get(pk=investment_project.id)
        assert set(
            [str(value.id) for value in stored_investment_project.delivery_partners.all()],
        ) == set([str(idp.id) for idp in idps])

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        ('simulate', 'delete', 'caplog_text'),
        [
            (
                False,
                False,
                "{'projects': {'count': 0, 'errors': []}, 'leps': {'investment_project_count': 3, 'to_delete': 0, 'deleted': 0, 'errors': []}, 'idps': {'investment_project_count': 0, 'to_add': 3, 'added': 3, 'errors': []}",
            ),
            (
                True,
                False,
                "{'projects': {'count': 0, 'errors': []}, 'leps': {'investment_project_count': 3, 'to_delete': 0, 'deleted': 0, 'errors': []}, 'idps': {'investment_project_count': 0, 'to_add': 3, 'added': 0, 'errors': []}",
            ),
            (
                False,
                True,
                "{'projects': {'count': 0, 'errors': []}, 'leps': {'investment_project_count': 3, 'to_delete': 3, 'deleted': 3, 'errors': []}, 'idps': {'investment_project_count': 0, 'to_add': 3, 'added': 3, 'errors': []}",
            ),
            (
                True,
                True,
                "{'projects': {'count': 0, 'errors': []}, 'leps': {'investment_project_count': 3, 'to_delete': 3, 'deleted': 0, 'errors': []}, 'idps': {'investment_project_count': 0, 'to_add': 3, 'added': 0, 'errors': []}",
            ),
        ],
    )
    def test_arguments(
        self,
        caplog: pytest.LogCaptureFixture,
        lep: InvestmentDeliveryPartner,
        idp: NoReturn,
        simulate,
        delete,
        caplog_text,
    ):
        """Test simulate and delete arguments."""
        caplog.set_level('INFO')

        leps = [
            lep,
            InvestmentDeliveryPartner.objects.get(pk='9abd575e-0af1-e511-8ffa-e4115bead28a'),
            InvestmentDeliveryPartner.objects.get(pk='87b87bf6-9f1a-e511-8e8f-441ea13961e2'),
            InvestmentDeliveryPartner.objects.get(pk='14ee950e-0bf1-e511-8ffa-e4115bead28a'),
        ]

        # idps
        InvestmentDeliveryPartnerFactory(id='182e76ca-868d-4ca4-a336-17a26719f786')
        InvestmentDeliveryPartnerFactory(id='dedd7553-63fe-41cc-874f-740d4cec8f97')

        InvestmentProjectFactory(
            actual_land_date=datetime(2025, 4, 1, tzinfo=timezone.utc),
            delivery_partners=leps,
        )

        call_command('update_investment_delivery_partners', simulate=simulate, delete=delete)

        assert caplog_text in caplog.text

    @pytest.mark.django_db
    def test_lep_does_not_exist(
        self,
        mocker,
        caplog: pytest.LogCaptureFixture,
        lep: InvestmentDeliveryPartner,
    ):
        """Test lep doesn't exist."""
        mocker.patch(
            'datahub.dbmaintenance.management.commands.update_investment_delivery_partners.delivery_partner_mappings',
            new=[
                {
                    'lep': 'abcdef01-09f1-e511-8ffa-e4115bead28a',  # non existing UUID
                    'idp': '4d2d0351-ffaa-4a0d-986a-f13be4ec2198',
                },
            ],
        )
        caplog.set_level('INFO')

        InvestmentProjectFactory(
            actual_land_date=datetime(2025, 4, 1, tzinfo=timezone.utc),
            delivery_partners=[lep],
        )

        call_command('update_investment_delivery_partners', simulate=False, delete=True)
        message = "{'projects': {'count': 0, 'errors': []}, 'leps': {'investment_project_count': 0, 'to_delete': 0, 'deleted': 0, 'errors': []}, 'idps': {'investment_project_count': 0, 'to_add': 0, 'added': 0, 'errors': []}"

        assert message in caplog.text

    @pytest.mark.django_db
    def test_idp_does_not_exist(
        self,
        mocker,
        caplog: pytest.LogCaptureFixture,
        lep: InvestmentDeliveryPartner,
    ):
        """Test idp doesn't exist."""
        idp_id = 'ef9520d0-4ac6-4afc-a7a5-f52a84d722cd'
        mocker.patch(
            'datahub.dbmaintenance.management.commands.update_investment_delivery_partners.delivery_partner_mappings',
            new=[
                {
                    'lep': lep.id,
                    'idp': idp_id,
                },
            ],
        )
        caplog.set_level('INFO')

        investment_project = InvestmentProjectFactory(
            actual_land_date=datetime(2025, 4, 1, tzinfo=timezone.utc),
            delivery_partners=[lep],
        )
        call_command('update_investment_delivery_partners', simulate=False, delete=True)

        message = (
            "{'projects': {'count': 0, 'errors': []}, 'leps': {'investment_project_count': 1, 'to_delete': 0, 'deleted': 0, 'errors': []}, 'idps': {'investment_project_count': 0, 'to_add': 1, 'added': 1, 'errors': ['Missing IDP "
            + str(idp_id)
            + ' on Investment project '
            + str(investment_project.id)
            + '; LEP '
            + str(lep.id)
            + " has not been removed.']}}"
        )
        assert message in caplog.text

        # Add missing idp to investment project to avoid post test issues causing IntegretyError in
        # investment_investmentdeliverypartner test_case._post_teardown().
        hack_idp = InvestmentDeliveryPartnerFactory(
            id='ef9520d0-4ac6-4afc-a7a5-f52a84d722cd',
            name='Hello world',
        )
        investment_project.delivery_partners.add(hack_idp)
        investment_project.save()
