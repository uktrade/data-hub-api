from dateutil.parser import parse as dateutil_parse

from datahub.investment.project.proposition.models import PropositionStatus
from datahub.investment.project.report.spi import SPIReport


class SPIReportFormatter:
    """
    SPI Report Formatter changes the format of the SPI Report.

    TODO: Once original SPI report is removed from Django admin, this format should be
    implemented in the report itself.
    """

    required_fields_label_mapping = {
        'Data Hub ID': 'investment_project_id',
        'Enquiry processed': 'enquiry_processed',
        'Enquiry type': 'enquiry_type',
        'Enquiry processed by ID': 'enquiry_processed_by_id',
        'Assigned to IST': 'assigned_to_ist',
        'Project manager assigned': 'project_manager_assigned',
        'Project manager assigned by': 'project_manager_assigned_by_id',
        'Project moved to won': 'project_moved_to_won',
        'Aftercare offered on': 'aftercare_offered_on',
        'Propositions': 'propositions',
    }

    required_fields_value_mapping = {
        'Project manager assigned by': lambda adviser: str(adviser.id) if adviser else '',
    }

    def __init__(self):
        """Initialise SPI Report Formatter."""
        self._SPIReport = SPIReport(proposition_formatter=proposition_formatter)

    def filter_fields(self, result):
        """Filter results fields."""
        return {
            self.required_fields_label_mapping[key]:
                self.required_fields_value_mapping.get(key, lambda value: value)(value)
            for key, value in result.items()
            if key in self.required_fields_label_mapping
        }

    def format(self, investment_projects):
        """
        Enrich Investment Project record with SPI report data and only include required fields.
        """
        for investment_project in investment_projects:
            spi_report_row = self._SPIReport.get_row(investment_project)
            result = self.filter_fields(spi_report_row)
            yield result


def proposition_formatter(propositions):
    """Returns a list of propositions with selected fields."""
    return [
        {
            'deadline': dateutil_parse(proposition['deadline']).strftime('%Y-%m-%d'),
            'status': proposition['status'],
            'modified_on':
                dateutil_parse(proposition['modified_on']).isoformat()
                if proposition['status'] != PropositionStatus.ONGOING else '',
            'adviser_id': proposition['adviser_id'],
        }
        for proposition in propositions
    ]
