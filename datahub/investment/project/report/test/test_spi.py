from unittest.mock import Mock

import pytest
from dateutil.parser import parse as dateutil_parse
from django.utils.timezone import now
from freezegun import freeze_time

from datahub.company.test.factories import AdviserFactory, TeamFactory
from datahub.core.constants import InvestmentProjectStage as InvestmentProjectStageConstant
from datahub.core.constants import Service as ServiceConstant
from datahub.core.test_utils import random_obj_for_queryset
from datahub.interaction.test.factories import InvestmentProjectInteractionFactory
from datahub.investment.project.constants import InvestorType as InvestorTypeConstant
from datahub.investment.project.proposition.models import PropositionDocument, PropositionStatus
from datahub.investment.project.proposition.test.factories import PropositionFactory
from datahub.investment.project.report.spi import (
    _filter_row_dicts,
    ALL_SPI_SERVICE_IDS,
    SPIReport,
    write_report,
)
from datahub.investment.project.test.factories import (
    InvestmentProjectFactory,
    VerifyWinInvestmentProjectFactory,
)
from datahub.metadata.models import Service
from datahub.metadata.models import Team

pytestmark = pytest.mark.django_db


@pytest.fixture
def spi_report():
    """Gets instance of SPI Report."""
    yield SPIReport()


@pytest.fixture
def ist_adviser():
    """Provides IST adviser."""
    team = TeamFactory(tags=[Team.Tag.INVESTMENT_SERVICES_TEAM])
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
    assert rows[0]['Enquiry processed'] == ''


@pytest.mark.parametrize(
    'service_id,visible',
    (
        (ServiceConstant.investment_enquiry_requested_more_information.value.id, True),
        (ServiceConstant.investment_enquiry_confirmed_prospect.value.id, True),
        (ServiceConstant.investment_enquiry_assigned_to_ist_cmc.value.id, True),
        (ServiceConstant.investment_enquiry_assigned_to_ist_sas.value.id, True),
        (ServiceConstant.investment_enquiry_assigned_to_hq.value.id, True),
        (ServiceConstant.investment_enquiry_transferred_to_lep.value.id, True),
        (ServiceConstant.investment_enquiry_transferred_to_da.value.id, True),
        (ServiceConstant.investment_enquiry_transferred_to_lp.value.id, True),
        (ServiceConstant.inbound_referral.value.id, False),
        (ServiceConstant.account_management.value.id, False),
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
        assert str(rows[0]['Enquiry processed by']) == interaction.created_by.name
        assert str(rows[0]['Enquiry processed by ID']) == str(interaction.created_by.id)
        assert rows[0]['Enquiry type'] == interaction.service.name
    else:
        assert rows[0]['Enquiry processed'] == ''
        assert rows[0]['Enquiry processed by'] == ''
        assert rows[0]['Enquiry processed by ID'] == ''
        assert rows[0]['Enquiry type'] == ''


@pytest.mark.parametrize(
    'service_id,visible',
    (
        (ServiceConstant.investment_enquiry_requested_more_information.value.id, False),
        (ServiceConstant.investment_enquiry_confirmed_prospect.value.id, False),
        (ServiceConstant.investment_enquiry_assigned_to_ist_cmc.value.id, True),
        (ServiceConstant.investment_enquiry_assigned_to_ist_sas.value.id, True),
        (ServiceConstant.investment_enquiry_assigned_to_hq.value.id, False),
        (ServiceConstant.investment_enquiry_transferred_to_lep.value.id, False),
        (ServiceConstant.investment_enquiry_transferred_to_da.value.id, False),
        (ServiceConstant.investment_enquiry_transferred_to_lp.value.id, False),
        (ServiceConstant.inbound_referral.value.id, False),
        (ServiceConstant.account_management.value.id, False),
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
        assert rows[0]['Assigned to IST'] == ''


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
    assert rows[0]['Project manager assigned'] == ''
    assert rows[0]['Project manager assigned by'] == ''


def test_earliest_interactions_are_being_selected(spi_report, ist_adviser):
    """Tests that report contains earliest interaction dates."""
    investment_project = InvestmentProjectFactory(
        project_manager=ist_adviser,
    )

    service_dates = (
        (ServiceConstant.investment_enquiry_confirmed_prospect.value.id, '2016-01-02'),
        (ServiceConstant.investment_enquiry_confirmed_prospect.value.id, '2016-01-03'),
        (ServiceConstant.investment_enquiry_confirmed_prospect.value.id, '2016-01-01'),
        (ServiceConstant.investment_enquiry_assigned_to_ist_sas.value.id, '2017-01-03'),
        (ServiceConstant.investment_enquiry_assigned_to_ist_sas.value.id, '2017-01-01'),
        (ServiceConstant.investment_enquiry_assigned_to_ist_sas.value.id, '2017-01-02'),
        (ServiceConstant.investment_ist_aftercare_offered.value.id, '2017-03-04'),
        (ServiceConstant.investment_ist_aftercare_offered.value.id, '2017-03-05'),
        (ServiceConstant.investment_ist_aftercare_offered.value.id, '2017-03-06'),
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


def test_only_ist_interactions_are_being_selected(spi_report, ist_adviser):
    """Tests that report takes into account IST interactions only."""
    investment_project = InvestmentProjectFactory(
        project_manager=ist_adviser,
    )

    service_dates = (
        (ServiceConstant.account_management.value.id, '2015-01-23'),
        (
            random_obj_for_queryset(Service.objects.exclude(pk__in=ALL_SPI_SERVICE_IDS)).id,
            '2015-12-03',
        ),
        (ServiceConstant.investment_enquiry_confirmed_prospect.value.id, '2016-01-02'),
        (
            random_obj_for_queryset(Service.objects.exclude(pk__in=ALL_SPI_SERVICE_IDS)).id,
            '2016-01-02',
        ),
        (
            random_obj_for_queryset(Service.objects.exclude(pk__in=ALL_SPI_SERVICE_IDS)).id,
            '2016-01-03',
        ),
        (ServiceConstant.investment_enquiry_confirmed_prospect.value.id, '2016-01-01'),
        (
            random_obj_for_queryset(Service.objects.exclude(pk__in=ALL_SPI_SERVICE_IDS)).id,
            '2017-01-01',
        ),
        (ServiceConstant.investment_enquiry_assigned_to_ist_sas.value.id, '2017-01-03'),
        (ServiceConstant.investment_ist_aftercare_offered.value.id, '2017-03-04'),
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
    assert rows[0]['Assigned to IST'] == '2017-01-03T00:00:00+00:00'
    assert rows[0]['Aftercare offered on'] == '2017-03-04T00:00:00+00:00'


def test_can_get_propositions_with_default_formatting(spi_report, propositions):
    """Check if we can see propositions in the report."""
    rows = list(spi_report.rows())

    assert len(rows) == 1

    expected = (
        '2017-01-05;ongoing;;John Doe',
        '2017-01-05;completed;2017-01-04T11:11:11+00:00;John Doe',
        '2017-01-05;abandoned;2017-01-04T11:11:11+00:00;John Doe',
    )
    assert rows[0]['Propositions'] == ';'.join(expected)


def test_can_get_propositions_with_custom_formatting(propositions):
    """Check if we can see custom formatted propositions in the report."""

    def proposition_formatter(propositions):
        return [{
            'deadline': dateutil_parse(proposition['deadline']).strftime('%Y-%m-%d'),
            'status': proposition['status'],
            'modified_on': dateutil_parse(proposition['modified_on']).isoformat()
            if proposition['status'] != PropositionStatus.ONGOING else '',
            'adviser_id': str(proposition['adviser_id']),
        } for proposition in propositions]

    spi_report = SPIReport(proposition_formatter=proposition_formatter)
    rows = list(spi_report.rows())

    assert len(rows) == 1

    expected = [
        {
            'deadline': '2017-01-05',
            'status': 'ongoing',
            'modified_on': '',
            'adviser_id': str(propositions[0].adviser.id),
        },
        {
            'deadline': '2017-01-05',
            'status': 'completed',
            'modified_on': '2017-01-04T11:11:11+00:00',
            'adviser_id': str(propositions[1].adviser.id),
        },
        {
            'deadline': '2017-01-05',
            'status': 'abandoned',
            'modified_on': '2017-01-04T11:11:11+00:00',
            'adviser_id': str(propositions[0].adviser.id),
        },
    ]
    assert rows[0]['Propositions'] == expected


def test_can_get_spi5_start_and_end(spi_report, ist_adviser):
    """Tests if we can see spi5 start and end dates."""
    investment_project = VerifyWinInvestmentProjectFactory(
        project_manager=ist_adviser,
    )

    with freeze_time('2017-01-01'):
        investment_project.stage_id = InvestmentProjectStageConstant.won.value.id
        investment_project.save()

    with freeze_time('2017-01-15'):
        InvestmentProjectInteractionFactory(
            service_id=ServiceConstant.investment_ist_aftercare_offered.value.id,
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
        investor_type_id=InvestorTypeConstant.existing_investor.value.id,
    )

    with freeze_time('2017-01-01'):
        investment_project.stage_id = InvestmentProjectStageConstant.won.value.id
        investment_project.save()

    with freeze_time('2017-01-15'):
        InvestmentProjectInteractionFactory(
            service_id=ServiceConstant.investment_ist_aftercare_offered.value.id,
            investment_project=investment_project,
        )

    rows = list(spi_report.rows())
    assert len(rows) == 1
    assert rows[0]['Project moved to won'] == ''
    assert rows[0]['Aftercare offered on'] == ''


def test_write_report(ist_adviser):
    """Test that SPI report CSV is generated correctly."""
    pm_assigned_by = AdviserFactory()
    pm_assigned_on = now()
    investment_project = VerifyWinInvestmentProjectFactory(
        project_manager=ist_adviser,
        project_manager_first_assigned_on=pm_assigned_on,
        project_manager_first_assigned_by=pm_assigned_by,
    )
    spi1 = InvestmentProjectInteractionFactory(
        investment_project=investment_project,
        service_id=ServiceConstant.investment_enquiry_requested_more_information.value.id,
    )
    spi2 = InvestmentProjectInteractionFactory(
        investment_project=investment_project,
        service_id=ServiceConstant.investment_enquiry_assigned_to_ist_cmc.value.id,
    )

    proposition = PropositionFactory(
        deadline='2017-01-05',
        status='ongoing',
        adviser=pm_assigned_by,
        investment_project=investment_project,
        created_by=ist_adviser,
    )

    investment_project.stage_id = InvestmentProjectStageConstant.won.value.id
    investment_project.save()

    spi5 = InvestmentProjectInteractionFactory(
        investment_project=investment_project,
        service_id=ServiceConstant.investment_ist_aftercare_offered.value.id,
    )

    lines = []
    file = Mock()
    file.write = lambda line: lines.append(line.decode('utf8'))
    write_report(file)

    headers = ','.join(SPIReport.field_titles.keys())
    assert lines[1] == f'{headers}\r\n'

    row = [
        str(investment_project.pk),
        investment_project.project_code,
        investment_project.name,
        investment_project.created_on.isoformat(),
        spi1.created_on.isoformat(),
        spi1.service.name,
        spi1.created_by.name,
        spi2.created_on.isoformat(),
        investment_project.project_manager_first_assigned_on.isoformat(),
        investment_project.project_manager_first_assigned_by.name,
        investment_project.stage_log.get(
            stage_id=InvestmentProjectStageConstant.won.value.id,
        ).created_on.isoformat(),
        spi5.created_on.isoformat(),
        f'{proposition.deadline};{proposition.status};;{proposition.adviser.name}',
    ]
    expected_line = ','.join(row)
    assert lines[2] == f'{expected_line}\r\n'


def test_filter_row_dicts():
    """Tests that row dicts will have keys, that are not in field items, excluded."""
    row_dicts = [
        {'a': 1, 'b': 2, 'c': 3},
        {'b': 5, 'e': 1},
        {'x': 4, 'z': 5},
        {'a': 1, 'b': 2},
    ]
    field_titles = ['a', 'b']

    filtered_row_dicts = list(_filter_row_dicts(row_dicts, field_titles))

    expected_row_dicts = [
        {'a': 1, 'b': 2},
        {'b': 5},
        {},
        {'a': 1, 'b': 2},
    ]
    assert filtered_row_dicts == expected_row_dicts
