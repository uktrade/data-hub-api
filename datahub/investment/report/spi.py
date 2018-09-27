"""
Investment project SPI report functions.

Service Performance Indicator report should have following metrics:

SPI1_START  - investment project created on date
SPI1_END    - earliest one of 8 SPI interactions
SPI2_START  - earliest one of 2 SPI interactions that starts SPI 2
SPI2_END    - when project manager was first assigned, only project managers from IST
SPI3        - formatted list of propositions, only created by IST
SPI5_START  - when project has been moved to won
SPI5_END    - earliest interaction when aftercare was offered, only for new investor,
              only for IST managed projects
"""

from datahub.core.constants import InvestmentProjectStage as Stage, Service
from datahub.core.csv import csv_iterator
from datahub.interaction.models import Interaction
from datahub.investment.constants import InvestorType
from datahub.investment.models import InvestmentProject
from datahub.investment.proposition.constants import PropositionStatus
from datahub.metadata.models import Team


def format_date(d):
    """Date format used in the report."""
    return d.isoformat()


def write_report(file):
    """Write CSV report."""
    spi_report = SPIReport()
    for line in csv_iterator(spi_report.rows(), spi_report.field_titles):
        file.write(line)


class SPIReport:
    """SPI Report."""

    SPI1_START = 'Project created on'
    SPI1_END = 'Enquiry processed'
    SPI2_START = 'Assigned to IST'
    SPI2_END = 'Project manager assigned'
    SPI3 = 'Propositions'
    SPI5_START = 'Project moved to won'
    SPI5_END = 'Aftercare offered on'

    SPI_PROJECT_ID = 'Project ID'
    SPI_DH_ID = 'Data Hub ID'
    SPI_NAME = 'Project name'

    field_titles = {
        SPI_DH_ID: SPI_DH_ID,
        SPI_PROJECT_ID: SPI_PROJECT_ID,
        SPI_NAME: SPI_NAME,
        SPI1_START: SPI1_START,
        SPI1_END: SPI1_END,
        SPI2_START: SPI2_START,
        SPI2_END: SPI2_END,
        SPI5_START: SPI5_START,
        SPI5_END: SPI5_END,
        SPI3: SPI3,
    }

    SPI1_END_SERVICE_IDS = {
        Service.investment_enquiry_requested_more_information.value.id,
        Service.investment_enquiry_confirmed_prospect.value.id,
        Service.investment_enquiry_assigned_to_ist_cmc.value.id,
        Service.investment_enquiry_assigned_to_ist_sas.value.id,
        Service.investment_enquiry_assigned_to_hq.value.id,
        Service.investment_enquiry_transferred_to_lep.value.id,
        Service.investment_enquiry_transferred_to_da.value.id,
        Service.investment_enquiry_transferred_to_lp.value.id,
    }

    SPI2_START_SERVICE_IDS = {
        Service.investment_enquiry_assigned_to_ist_cmc.value.id,
        Service.investment_enquiry_assigned_to_ist_sas.value.id,
    }

    SPI5_END_SERVICE_IDS = {
        Service.investment_ist_aftercare_offered.value.id,
    }

    MAPPINGS = (
        (SPI1_END_SERVICE_IDS, SPI1_END),
        (SPI2_START_SERVICE_IDS, SPI2_START),
        (SPI5_END_SERVICE_IDS, SPI5_END),
    )

    def _get_spi_interactions(self, investment_project):
        """
        Gets SPI interactions for given Investment Project.

        Takes earliest interaction for each SPI, if available.
        """
        all_service_ids = (
            self.SPI1_END_SERVICE_IDS
            | self.SPI2_START_SERVICE_IDS
            | self.SPI5_END_SERVICE_IDS
        )

        interactions = Interaction.objects.filter(
            investment_project_id=investment_project.id,
            service_id__in=all_service_ids,
        ).order_by('created_on')

        data = {}
        for interaction in interactions:
            for service_ids, field_name in self.MAPPINGS:
                if (
                    str(interaction.service_id) in service_ids
                    and field_name not in data
                ):
                    data[field_name] = format_date(interaction.created_on)

        return data

    def _has_ist_project_manager(self, investment_project):
        """Checks if investment project has an IST project manager."""
        project_manager = investment_project.project_manager
        return (
            project_manager
            and project_manager.dit_team
            and Team.TAGS.investment_services_team in project_manager.dit_team.tags
        )

    def _find_when_project_moved_to_won(self, investment_project):
        """
        Finds when project has been moved to Won stage.

        Earliest date counts.
        """
        stage_log = investment_project.stage_log.filter(
            stage_id=Stage.won.value.id,
        ).order_by('created_on').first()

        return stage_log.created_on if stage_log else None

    def _get_propositions(self, investment_project, ist_only=False):
        """Gets project's propositions."""
        qs = investment_project.proposition.select_related(
            'adviser',
            'created_by__dit_team',
        )
        if ist_only:
            # Only teams tagged with investment services team
            qs = qs.filter(
                created_by__dit_team__tags__overlap=[Team.TAGS.investment_services_team],
            )
        return qs.order_by('created_on')

    def _format_propositions(self, propositions):
        """
        Formats propositions.

        Propositions need to be presented in the cell in following format:

        deadline;ongoing;;adviser.name;deadline;completed;modified_on;adviser.name...
        """
        formatted = []

        for proposition in propositions:
            formatted.append(proposition.deadline.isoformat())
            formatted.append(proposition.status)
            if proposition.status == PropositionStatus.ongoing:
                modified_on = ''
            else:
                modified_on = proposition.modified_on.isoformat()
            formatted.append(modified_on)
            formatted.append(proposition.adviser.name)

        return ';'.join(formatted)

    def _enrich_row(self, investment_project, spi_data=None):
        """Enriches the spi report with investment project details."""
        if spi_data is None:
            spi_data = {}

        spi_data[self.SPI_DH_ID] = str(investment_project.id)
        spi_data[self.SPI_PROJECT_ID] = investment_project.project_code
        spi_data[self.SPI_NAME] = investment_project.name
        return spi_data

    def get_spi1(self, investment_project, spi_interaction_dates):
        """Update data with SPI 1 dates."""
        data = {}

        data[self.SPI1_START] = format_date(investment_project.created_on)
        if self.SPI1_END in spi_interaction_dates:
            data[self.SPI1_END] = spi_interaction_dates[self.SPI1_END]

        return data

    def get_spi2(self, investment_project, spi_interaction_dates):
        """Update data with SPI 2 dates."""
        data = {}

        has_ist_pm = self._has_ist_project_manager(investment_project)

        if self.SPI2_START in spi_interaction_dates:
            data[self.SPI2_START] = spi_interaction_dates[self.SPI2_START]

        if has_ist_pm and investment_project.project_manager_first_assigned_on:
            data[self.SPI2_END] = format_date(investment_project.project_manager_first_assigned_on)

        return data

    def get_spi3(self, investment_project):
        """Update data with SPI 3 propositions."""
        data = {}

        propositions = self._get_propositions(investment_project, ist_only=True)
        if propositions:
            data[self.SPI3] = self._format_propositions(propositions)

        return data

    def get_spi5(self, investment_project, spi_interaction_dates):
        """Update data with SPI 5 dates."""
        data = {}

        has_ist_pm = self._has_ist_project_manager(investment_project)
        new_investor_id = InvestorType.new_investor.value.id
        is_new_investor = str(investment_project.investor_type_id) == new_investor_id

        if has_ist_pm and is_new_investor:
            moved_to_won = self._find_when_project_moved_to_won(investment_project)
            if moved_to_won:
                data[self.SPI5_START] = format_date(moved_to_won)

            if self.SPI5_END in spi_interaction_dates:
                data[self.SPI5_END] = spi_interaction_dates[self.SPI5_END]

        return data

    def get_spi_data_for_investment_project(self, investment_project):
        """Gets all SPI data for investment project."""
        spi_interaction_dates = self._get_spi_interactions(investment_project)

        data = {}
        data.update(self.get_spi1(investment_project, spi_interaction_dates))
        data.update(self.get_spi2(investment_project, spi_interaction_dates))
        data.update(self.get_spi3(investment_project))
        data.update(self.get_spi5(investment_project, spi_interaction_dates))

        return data

    def get_row(self, investment_project):
        """Gets SPI report row for given investment project."""
        spi_data = self.get_spi_data_for_investment_project(investment_project)
        spi_data = self._enrich_row(investment_project, spi_data)
        return spi_data

    def rows(self):
        """Return SPI report iterator."""
        for investment_project in InvestmentProject.objects.order_by('created_on').iterator():
            yield self.get_row(investment_project)
