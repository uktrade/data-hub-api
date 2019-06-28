import pytest
from django.utils.timezone import now
from freezegun import freeze_time

from datahub.company.test.factories import AdviserFactory, TeamFactory
from datahub.core.constants import InvestmentProjectStage
from datahub.core.constants import Service
from datahub.interaction.test.factories import InvestmentProjectInteractionFactory
from datahub.investment.project.constants import InvestorType
from datahub.investment.project.proposition.models import PropositionDocument
from datahub.investment.project.proposition.test.factories import PropositionFactory
from datahub.investment.project.report.spi import SPIReport
from datahub.investment.project.test.factories import (
    InvestmentProjectFactory,
    VerifyWinInvestmentProjectFactory,
)
from datahub.metadata.models import Team

pytestmark = pytest.mark.django_db


@pytest.fixture
def spi_report():
    """Gets instance of SPI Report."""
    yield SPIReport()


@pytest.fixture
def ist_adviser():
    """Provides IST adviser."""
    team = TeamFactory(tags=[Team.TAGS.investment_services_team])
    yield AdviserFactory(dit_team_id=team.id)


@pytest.fixture
def propositions(ist_adviser):
    """Gets variety of propositions."""
    investment_project = InvestmentProjectFactory(
        project_manager=ist_adviser,
    )
    adviser = AdviserFactory(
        first_name='John',
        last_name='Doe',
    )
    items = [
        PropositionFactory(
            deadline='2017-01-05',
            status='ongoing',
            adviser=adviser,
            investment_project=investment_project,
            created_by=ist_adviser,
        ),
        PropositionFactory(
            deadline='2017-01-05',
            status='ongoing',
            adviser=adviser,
            investment_project=investment_project,
            created_by=ist_adviser,
        ),
        PropositionFactory(
            deadline='2017-01-05',
            status='ongoing',
            adviser=adviser,
            investment_project=investment_project,
            created_by=ist_adviser,
        ),
    ]

    with freeze_time('2017-01-04 11:11:11'):
        entity_document = PropositionDocument.objects.create(
            proposition_id=items[1].pk,
            original_filename='test.txt',
            created_by=adviser,
        )
        entity_document.document.mark_as_scanned(True, '')
        items[1].complete(by=adviser, details='what')

        items[2].abandon(by=adviser, details='what')

    yield items


def test_can_see_spi1_start(spi_report):
    """Checks if creation of Investment Project starts SPI 1"""
    investment_project = InvestmentProjectFactory()

    rows = list(spi_report.rows())

    assert len(rows) == 1
    assert rows[0]['Project created on'] == investment_project.created_on.isoformat()
    assert 'Enquiry processed' not in rows[0]


@pytest.mark.parametrize(
    'service_id,visible',
    (
        (Service.investment_enquiry_requested_more_information.value.id, True),
        (Service.investment_enquiry_confirmed_prospect.value.id, True),
        (Service.investment_enquiry_assigned_to_ist_cmc.value.id, True),
        (Service.investment_enquiry_assigned_to_ist_sas.value.id, True),
        (Service.investment_enquiry_assigned_to_hq.value.id, True),
        (Service.investment_enquiry_transferred_to_lep.value.id, True),
        (Service.investment_enquiry_transferred_to_da.value.id, True),
        (Service.investment_enquiry_transferred_to_lp.value.id, True),
        (Service.inbound_referral.value.id, False),
        (Service.account_management.value.id, False),
    ),
)
def test_interaction_would_end_spi1_or_not(spi_report, service_id, visible):
    """Checks if specified interaction ends spi1 or not."""
    investment_project = InvestmentProjectFactory()
    interaction = InvestmentProjectInteractionFactory(
        investment_project=investment_project,
        service_id=service_id,
    )

    rows = list(spi_report.rows())

    assert len(rows) == 1
    assert rows[0]['Project created on'] == investment_project.created_on.isoformat()
    if visible:
        assert rows[0]['Enquiry processed'] == interaction.created_on.isoformat()
        assert rows[0]['Enquiry processed by'] == interaction.created_by.name
        assert rows[0]['Enquiry type'] == interaction.service.name
    else:
        assert 'Enquiry processed' not in rows[0]
        assert 'Enquiry processed by' not in rows[0]
        assert 'Enquiry type' not in rows[0]


@pytest.mark.parametrize(
    'service_id,visible',
    (
        (Service.investment_enquiry_requested_more_information.value.id, False),
        (Service.investment_enquiry_confirmed_prospect.value.id, False),
        (Service.investment_enquiry_assigned_to_ist_cmc.value.id, True),
        (Service.investment_enquiry_assigned_to_ist_sas.value.id, True),
        (Service.investment_enquiry_assigned_to_hq.value.id, False),
        (Service.investment_enquiry_transferred_to_lep.value.id, False),
        (Service.investment_enquiry_transferred_to_da.value.id, False),
        (Service.investment_enquiry_transferred_to_lp.value.id, False),
        (Service.inbound_referral.value.id, False),
        (Service.account_management.value.id, False),
    ),
)
def test_interaction_would_start_spi2_or_not(spi_report, ist_adviser, service_id, visible):
    """Checks if specified interaction starts spi2 or not."""
    investment_project = InvestmentProjectFactory(
        project_manager=ist_adviser,
    )
    interaction = InvestmentProjectInteractionFactory(
        investment_project=investment_project,
        service_id=service_id,
    )

    rows = list(spi_report.rows())

    assert len(rows) == 1
    if visible:
        assert rows[0]['Assigned to IST'] == interaction.created_on.isoformat()
    else:
        assert 'Assigned to IST' not in rows[0]


def test_assigning_ist_project_manager_ends_spi2(spi_report, ist_adviser):
    """Test if assigning IST project manager would end SPI 2."""
    investment_project = InvestmentProjectFactory()
    investment_project.project_manager = ist_adviser
    adviser = AdviserFactory()
    investment_project.project_manager_first_assigned_on = now()
    investment_project.project_manager_first_assigned_by = adviser
    investment_project.save()

    rows = list(spi_report.rows())

    assert len(rows) == 1
    assigned_on = investment_project.project_manager_first_assigned_on
    assert rows[0]['Project manager assigned'] == assigned_on.isoformat()
    assert rows[0]['Project manager assigned by'] == adviser


def test_assigning_non_ist_project_manager_doesnt_end_spi2(spi_report):
    """Test that non IST project manager wont end SPI 2."""
    investment_project = InvestmentProjectFactory()
    investment_project.project_manager = AdviserFactory()
    investment_project.project_manager_first_assigned_on = now()
    investment_project.project_manager_first_assigned_by = AdviserFactory()
    investment_project.save()

    rows = list(spi_report.rows())

    assert len(rows) == 1
    assert 'Project manager assigned' not in rows[0]
    assert 'Project manager assigned by' not in rows[0]


def test_earliest_interactions_are_being_selected(spi_report, ist_adviser):
    """Tests that report contains earliest interaction dates."""
    investment_project = InvestmentProjectFactory(
        project_manager=ist_adviser,
    )

    service_dates = (
        (Service.investment_enquiry_confirmed_prospect.value.id, '2016-01-02'),
        (Service.investment_enquiry_confirmed_prospect.value.id, '2016-01-03'),
        (Service.investment_enquiry_confirmed_prospect.value.id, '2016-01-01'),
        (Service.investment_enquiry_assigned_to_ist_sas.value.id, '2017-01-03'),
        (Service.investment_enquiry_assigned_to_ist_sas.value.id, '2017-01-01'),
        (Service.investment_enquiry_assigned_to_ist_sas.value.id, '2017-01-02'),
        (Service.investment_ist_aftercare_offered.value.id, '2017-03-04'),
        (Service.investment_ist_aftercare_offered.value.id, '2017-03-05'),
        (Service.investment_ist_aftercare_offered.value.id, '2017-03-06'),
    )
    for service_date in service_dates:
        with freeze_time(service_date[1]):
            InvestmentProjectInteractionFactory(
                investment_project=investment_project,
                service_id=service_date[0],
            )

    rows = list(spi_report.rows())

    assert len(rows) == 1
    assert rows[0]['Enquiry processed'] == '2016-01-01T00:00:00+00:00'
    assert rows[0]['Assigned to IST'] == '2017-01-01T00:00:00+00:00'
    assert rows[0]['Aftercare offered on'] == '2017-03-04T00:00:00+00:00'


def test_can_get_propositions(spi_report, propositions):
    """Check if we can see propositions in the report."""
    rows = list(spi_report.rows())

    assert len(rows) == 1

    expected = (
        '2017-01-05;ongoing;;John Doe',
        '2017-01-05;completed;2017-01-04T11:11:11+00:00;John Doe',
        '2017-01-05;abandoned;2017-01-04T11:11:11+00:00;John Doe',
    )
    assert rows[0]['Propositions'] == ';'.join(expected)


def test_can_get_spi5_start_and_end(spi_report, ist_adviser):
    """Tests if we can see spi5 start and end dates."""
    investment_project = VerifyWinInvestmentProjectFactory(
        project_manager=ist_adviser,
    )

    with freeze_time('2017-01-01'):
        investment_project.stage_id = InvestmentProjectStage.won.value.id
        investment_project.save()

    with freeze_time('2017-01-15'):
        InvestmentProjectInteractionFactory(
            service_id=Service.investment_ist_aftercare_offered.value.id,
            investment_project=investment_project,
        )

    rows = list(spi_report.rows())
    assert len(rows) == 1
    assert rows[0]['Project moved to won'] == '2017-01-01T00:00:00+00:00'
    assert rows[0]['Aftercare offered on'] == '2017-01-15T00:00:00+00:00'


def test_cannot_get_spi5_start_and_end_for_non_new_investor(
    spi_report,
    ist_adviser,
):
    """Tests if we are not going to see spi5 start and end dates if investor is not new."""
    investment_project = VerifyWinInvestmentProjectFactory(
        project_manager=ist_adviser,
        investor_type_id=InvestorType.existing_investor.value.id,
    )

    with freeze_time('2017-01-01'):
        investment_project.stage_id = InvestmentProjectStage.won.value.id
        investment_project.save()

    with freeze_time('2017-01-15'):
        InvestmentProjectInteractionFactory(
            service_id=Service.investment_ist_aftercare_offered.value.id,
            investment_project=investment_project,
        )

    rows = list(spi_report.rows())
    assert len(rows) == 1
    assert 'Project moved to won' not in rows[0]
    assert 'Aftercare offered on' not in rows[0]
