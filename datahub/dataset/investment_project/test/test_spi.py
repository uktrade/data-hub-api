from uuid import uuid4

import pytest

from datahub.company.test.factories import AdviserFactory
from datahub.dataset.investment_project.spi import proposition_formatter, SPIReportFormatter
from datahub.investment.project.proposition.models import PropositionStatus

pytestmark = pytest.mark.django_db


def test_spi_record_row_is_formatted():
    """Test that SPI record row is being formatted correctly."""
    formatter = SPIReportFormatter()
    spi_report_row = {
        'Project created on': 'project_created_on',
        'Enquiry processed': 'enquiry_processed',
        'Enquiry type': 'enquiry_type',
        'Enquiry processed by': str(AdviserFactory().id),
        'Assigned to IST': 'assigned_to_ist',
        'Project manager assigned': 'project_manager_assigned',
        'Project manager assigned by': str(AdviserFactory().id),
        'Propositions': [{
            'deadline': 'deadline',
            'status': 'status',
            'modified_on': 'modified_on',
            'adviser_id': 'adviser_id',
        }],
        'Project moved to won': 'project_moved_to_won',
        'Aftercare offered on': 'aftercare_offered_on',
        'Project ID': 'project_id',
        'Data Hub ID': 'data_hub_id',
        'Project name': 'project_name',
    }
    filtered_row = formatter.filter_fields(spi_report_row)
    assert filtered_row == {
        'enquiry_processed': 'enquiry_processed',
        'enquiry_type': 'enquiry_type',
        'enquiry_processed_by_id': spi_report_row['Enquiry processed by'],
        'assigned_to_ist': 'assigned_to_ist',
        'project_manager_assigned': 'project_manager_assigned',
        'project_manager_assigned_by_id': spi_report_row['Project manager assigned by'],
        'propositions': [{
            'deadline': 'deadline',
            'status': 'status',
            'modified_on': 'modified_on',
            'adviser_id': 'adviser_id',
        }],
        'project_moved_to_won': 'project_moved_to_won',
        'aftercare_offered_on': 'aftercare_offered_on',
        'investment_project_id': 'data_hub_id',
    }


def test_proposition_formatter():
    """Test that propositions are being formatted correctly."""
    propositions = [
        {
            'deadline': '2010-02-01T00:00:00+00:00',
            'modified_on': '2010-02-02T00:00:00+00:00',
            'status': PropositionStatus.ongoing,
            'adviser_id': uuid4(),
        },
        {
            'deadline': '2010-02-01T00:00:00+00:00',
            'modified_on': '2010-02-02T00:00:00+00:00',
            'status': PropositionStatus.completed,
            'adviser_id': uuid4(),
        },
    ]

    formatted_propositions = proposition_formatter(propositions)

    assert formatted_propositions == [
        {
            'deadline': '2010-02-01',
            'modified_on': '',
            'status': PropositionStatus.ongoing,
            'adviser_id': propositions[0]['adviser_id'],
        },
        {
            'deadline': '2010-02-01',
            'modified_on': '2010-02-02T00:00:00+00:00',
            'status': PropositionStatus.completed,
            'adviser_id': propositions[1]['adviser_id'],
        },
    ]
