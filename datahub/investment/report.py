from django.db.models import Prefetch

from datahub.core.constants import InvestmentProjectStage
from datahub.interaction.models import (
    Interaction
)
from datahub.investment.models import (
    InvestmentProject,
    InvestmentProjectSPIReportConfiguration,
    InvestmentProjectStageLog,
)


def get_investment_projects_in_active_stage(configuration, month, year):
    """Get Investment Projects moved to Active stage for given month."""
    stage_log = InvestmentProjectStageLog.objects.prefetch_related(
        'investment_project'
    ).filter(
        stage_id=InvestmentProjectStage.active.value.id,
        created_on__month=month,
        created_on__year=year,
    ).order_by('investment_project_id', '-created_on').distinct('investment_project_id')

    for stage in stage_log:
        yield {
            'id': stage.investment_project.id,
            'name': stage.investment_project.name,
            'project_code': stage.investment_project.project_code,
            'email_received_date': None,    # we don't have that data
            'moved_to_active_on': stage.created_on,
        }


def get_investment_projects_in_verify_win_stage(configuration, month, year):
    """Get Investment Projects moved to Verify Win stage for given month."""
    stage_log = InvestmentProjectStageLog.objects.prefetch_related(
        'investment_project'
    ).filter(
        stage_id=InvestmentProjectStage.verify_win.value.id,
        created_on__month=month,
        created_on__year=year,
    ).order_by('investment_project_id', '-created_on').distinct('investment_project_id')

    for stage in stage_log:
        yield {
            'id': stage.investment_project.id,
            'name': stage.investment_project.name,
            'project_code': stage.investment_project.project_code,
            'moved_to_verify_win': stage.created_on,
            'share_point_evidence': None,   # We don't have that data
        }


def get_investment_projects_with_pm_assigned(configuration, month, year):
    """
    Get PM assigned interaction for given month and corresponding
    date of stage change to Assign PM.
    """
    interactions = Interaction.objects.prefetch_related(
        'investment_project', 'investment_project__stage_log'
    ).filter(
        service_id=configuration.project_manager_assigned_id,
        date__month=month,
        date__year=year
    ).order_by('investment_project_id', 'date').distinct('investment_project_id')

    for interaction in interactions:
        # find when project was moved to "Assign PM" stage.
        stage = interaction.investment_project.stage_log.filter(
            stage_id=InvestmentProjectStage.assign_pm.value.id
        ).order_by('created_on').first()

        yield {
            'id': interaction.investment_project_id,
            'project_code': interaction.investment_project.project_code,
            'name': interaction.investment_project.name,
            'project_manager_assigned_on': stage.created_on if stage else None,
            'project_manager_assigned_notification_on': interaction.date,
        }


def get_investment_projects_with_proposal_deadline(configuration, month, year):
    """Get client proposal for given month and corresponding proposal deadline."""
    interactions = Interaction.objects.prefetch_related(
        'investment_project'
    ).filter(
        service_id=configuration.client_proposal_id,
        date__month=month,
        date__year=year
    ).order_by('investment_project_id', 'date').distinct('investment_project_id')

    for interaction in interactions:
        yield {
            'id': interaction.investment_project.id,
            'project_code': interaction.investment_project.project_code,
            'name': interaction.investment_project.name,
            'proposal_deadline': interaction.investment_project.proposal_deadline,
            'proposal_notification_on': interaction.date,
        }


def get_investment_projects_by_actual_land_date(configuration, month, year):
    """
    Get investment projects by actual land date and their corresponding
    interaction.
    """
    interactions = Interaction.objects.filter(
        service_id=configuration.after_care_offered_id
    ).order_by('-created_on')
    prefetch = Prefetch(
        'interactions',
        queryset=interactions,
        to_attr='first_after_care_offered'
    )
    investment_projects = InvestmentProject.objects.prefetch_related(
        prefetch
    ).filter(
        actual_land_date__month=month,
        actual_land_date__year=year,
    ).order_by('actual_land_date')

    for investment_project in investment_projects:
        interaction = investment_project.first_after_care_offered[0]
        yield {
            'id': investment_project.id,
            'project_code': investment_project.project_code,
            'name': investment_project.name,
            'actual_land_date': investment_project.actual_land_date,
            'first_after_care_offered_on': interaction.date if interaction else None,
        }


def generate_spi_report(month, year):
    """Generates SPI report."""
    configuration = InvestmentProjectSPIReportConfiguration.objects.first()

    report = {}

    get_investment_projects_fns = (
        get_investment_projects_in_active_stage,
        get_investment_projects_in_verify_win_stage,
        get_investment_projects_with_pm_assigned,
        get_investment_projects_with_proposal_deadline,
        get_investment_projects_by_actual_land_date,
    )

    for get_investment_projects_fn in get_investment_projects_fns:
        for row in get_investment_projects_fn(configuration, month, year):
            report[row['id']] = {**report.get(row['id'], {}), **row}

    yield from report.values()


def get_spi_report_fieldnames():
    """Gets SPI Report field names."""
    return {
        'id': 'Project ID',
        'project_code': 'Project Code',
        'name': 'Project Name',
        'email_received_date': 'Email received date',
        'moved_to_active_on': 'Date moved to active',
        'project_manager_assigned_on': 'Date moved to assign PM',
        'project_manager_notification_on': 'Date of notification that PM assigned',
        'proposal_deadline': 'Proposal deadline date',
        'proposal_notification_on': 'Date of proposal sent',
        'moved_to_verify_win': 'Verify win date',
        'sharepoint evidence': 'Sharepoint evidence',
        'actual_land_date': 'Actual Land date',
        'first_after_care_offered_on': 'Aftercare Offered Date',
    }
