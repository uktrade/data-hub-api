"""Tests for report."""

from unittest import mock

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time

from datahub.core import constants
from datahub.interaction.test.factories import (
    InvestmentProjectInteractionFactory
)
from datahub.investment.models import (
    InvestmentProjectStage
)
from datahub.investment.report import (
    generate_spi_report,
    get_investment_projects_by_actual_land_date,
    get_investment_projects_in_active_stage,
    get_investment_projects_in_verify_win_stage,
    get_investment_projects_with_pm_assigned,
    get_investment_projects_with_proposal_deadline,
)
from datahub.investment.test.factories import (
    InvestmentProjectFactory,
    InvestmentProjectSPIReportConfigurationFactory
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def investment_project_spi_report_configuration():
    """Creates investment project SPI report configuration."""
    return InvestmentProjectSPIReportConfigurationFactory(
        after_care_offered_id=constants.Service.trade_enquiry.value.id,
        project_manager_assigned_id=constants.Service.account_management.value.id,
        client_proposal_id=constants.Service.trade_enquiry.value.id,
    )


def test_get_investment_projects_in_active_stage(
    investment_project_spi_report_configuration
):
    """Tests getting investment projects in active stage."""
    with freeze_time('2017-01-05'):
        ip1 = InvestmentProjectFactory()
        ip1.stage_id = InvestmentProjectStage.active.value.id
        ip1.save()

    with freeze_time('2017-02-10'):
        ip2 = InvestmentProjectFactory()
        ip2.stage_id = InvestmentProjectStage.active.value.id
        ip2.save()
        ip2.stage_id = InvestmentProjectStage.prospect.value.id
        ip2.save()

    # to make sure we get the latest date when project moved to active stage
    with freeze_time('2017-02-11'):
        ip2.stage_id = InvestmentProjectStage.active.value.id
        ip2.save()

    items = get_investment_projects_in_active_stage(
        investment_project_spi_report_configuration,
        2,
        2017
    )

    stage_log = ip2.stage_log.filter(
        stage_id=ip2.stage_id
    ).order_by('-created_on').first()
    assert [
        {
            'id': ip2.id,
            'name': ip2.name,
            'project_code': ip2.project_code,
            'email_received_date': None,
            'moved_to_active_on': stage_log.created_on,
        }
    ] == [item for item in items]


def test_get_investment_projects_in_verify_win_stage(
    investment_project_spi_report_configuration
):
    """Tests getting investment projects in verify stage."""
    with freeze_time('2017-01-05'):
        ip1 = InvestmentProjectFactory()
        ip1.stage_id = InvestmentProjectStage.verify_win.value.id
        ip1.save()

    with freeze_time('2017-02-10'):
        ip2 = InvestmentProjectFactory()
        ip2.stage_id = InvestmentProjectStage.verify_win.value.id
        ip2.save()
        ip2.stage_id = InvestmentProjectStage.active.value.id
        ip2.save()

    # to make sure we get the latest date when project moved to verify win stage
    with freeze_time('2017-02-11'):
        ip2.stage_id = InvestmentProjectStage.verify_win.value.id
        ip2.save()

    items = get_investment_projects_in_verify_win_stage(
        investment_project_spi_report_configuration,
        2,
        2017
    )

    stage_log = ip2.stage_log.filter(
        stage_id=ip2.stage_id
    ).order_by('-created_on').first()
    assert [
        {
            'id': ip2.id,
            'name': ip2.name,
            'project_code': ip2.project_code,
            'moved_to_verify_win': stage_log.created_on,
            'share_point_evidence': None,
        }
    ] == [item for item in items]


def test_get_investment_projects_with_pm_assigned(
    investment_project_spi_report_configuration
):
    """
    Tests getting investment projects with assign pm stage and
    corresponding interaction date.
    """
    with freeze_time('2017-01-05') as mocked_now:
        ip1 = InvestmentProjectFactory()
        ip1.stage_id = InvestmentProjectStage.assign_pm.value.id
        ip1.save()
        InvestmentProjectInteractionFactory(
            investment_project=ip1,
            service_id=investment_project_spi_report_configuration.project_manager_assigned_id,
            date=mocked_now().replace(tzinfo=utc),
        )

    with freeze_time('2017-02-10') as mocked_now:
        ip2 = InvestmentProjectFactory()
        ip2.stage_id = InvestmentProjectStage.assign_pm.value.id
        ip2.save()
        ip2.stage_id = InvestmentProjectStage.prospect.value.id
        ip2.save()
        interaction2 = InvestmentProjectInteractionFactory(
            investment_project=ip2,
            service_id=investment_project_spi_report_configuration.project_manager_assigned_id,
            date=mocked_now().replace(tzinfo=utc),
        )

    # to make sure we get the earliest date when project moved to assign pm stage
    # and earliest interaction
    with freeze_time('2017-02-11') as mocked_now:
        ip2.stage_id = InvestmentProjectStage.assign_pm.value.id
        ip2.save()
        InvestmentProjectInteractionFactory(
            investment_project=ip2,
            service_id=investment_project_spi_report_configuration.project_manager_assigned_id,
            date=mocked_now().replace(tzinfo=utc),
        )

    items = get_investment_projects_with_pm_assigned(
        investment_project_spi_report_configuration,
        2,
        2017
    )

    stage_log = ip2.stage_log.filter(
        stage_id=ip2.stage_id
    ).order_by('created_on').first()
    assert [
        {
            'id': ip2.id,
            'name': ip2.name,
            'project_code': ip2.project_code,
            'project_manager_assigned_on': stage_log.created_on,
            'project_manager_assigned_notification_on': interaction2.date,
        }
    ] == [item for item in items]


def test_get_investment_projects_with_proposal_deadline(
    investment_project_spi_report_configuration
):
    """
    Tests getting investment projects with proposal deadline on given month and
    corresponding interaction date.
    """
    with freeze_time('2017-01-05') as mocked_now:
        ip1 = InvestmentProjectFactory(
            proposal_deadline=mocked_now().date()
        )
        InvestmentProjectInteractionFactory(
            investment_project=ip1,
            service_id=investment_project_spi_report_configuration.client_proposal_id,
            date=mocked_now().replace(tzinfo=utc),
        )

    with freeze_time('2017-02-10') as mocked_now:
        ip2 = InvestmentProjectFactory(
            proposal_deadline=mocked_now().date()
        )
        interaction2 = InvestmentProjectInteractionFactory(
            investment_project=ip2,
            service_id=investment_project_spi_report_configuration.client_proposal_id,
            date=mocked_now().replace(tzinfo=utc),
        )

    # to make sure we get the earliest interaction
    with freeze_time('2017-02-11') as mocked_now:
        InvestmentProjectInteractionFactory(
            investment_project=ip2,
            service_id=investment_project_spi_report_configuration.client_proposal_id,
            date=mocked_now().replace(tzinfo=utc),
        )

    items = get_investment_projects_with_proposal_deadline(
        investment_project_spi_report_configuration,
        2,
        2017
    )

    assert [
        {
            'id': ip2.id,
            'name': ip2.name,
            'project_code': ip2.project_code,
            'proposal_deadline': ip2.proposal_deadline,
            'proposal_notification_on': interaction2.date,
        }
    ] == [item for item in items]


def test_get_investment_projects_by_actual_land_date(
    investment_project_spi_report_configuration
):
    """
    Tests getting investment projects with actual land date on given month and
    corresponding interaction date.
    """
    with freeze_time('2017-01-05') as mocked_now:
        ip1 = InvestmentProjectFactory(
            actual_land_date=mocked_now().date()
        )
        InvestmentProjectInteractionFactory(
            investment_project=ip1,
            service_id=investment_project_spi_report_configuration.after_care_offered_id,
            date=mocked_now().replace(tzinfo=utc),
        )

    with freeze_time('2017-02-10') as mocked_now:
        ip2 = InvestmentProjectFactory(
            actual_land_date=mocked_now().date()
        )
        InvestmentProjectInteractionFactory(
            investment_project=ip2,
            service_id=investment_project_spi_report_configuration.after_care_offered_id,
            date=mocked_now().replace(tzinfo=utc),
        )

    with freeze_time('2017-02-11') as mocked_now:
        interaction2 = InvestmentProjectInteractionFactory(
            investment_project=ip2,
            service_id=investment_project_spi_report_configuration.after_care_offered_id,
            date=mocked_now().replace(tzinfo=utc),
        )

    items = get_investment_projects_by_actual_land_date(
        investment_project_spi_report_configuration,
        2,
        2017
    )

    assert [
        {
            'id': ip2.id,
            'name': ip2.name,
            'project_code': ip2.project_code,
            'actual_land_date': ip2.actual_land_date,
            'first_after_care_offered_on': interaction2.date,
        }
    ] == [item for item in items]


@mock.patch('datahub.investment.report.get_investment_projects_in_active_stage')
@mock.patch('datahub.investment.report.get_investment_projects_in_verify_win_stage')
@mock.patch('datahub.investment.report.get_investment_projects_with_pm_assigned')
@mock.patch('datahub.investment.report.get_investment_projects_with_proposal_deadline')
@mock.patch('datahub.investment.report.get_investment_projects_by_actual_land_date')
def test_can_create_report(
    mocked_by_actual_land_date,
    mocked_with_proposal_deadline,
    mocked_with_pm_assigned,
    mocked_in_verify_win_stage,
    mocked_in_active_stage,
    investment_project_spi_report_configuration,
):
    """Tests if we can create a report."""
    mocked_in_active_stage.return_value = iter(({
        'id': 2,
        'name': 'test',
        'project_code': '123',
        'email_received_date': None,
        'moved_to_active_on': '2017-10-11',
    },))

    mocked_in_verify_win_stage.return_value = iter(({
        'id': 1,
        'name': 'test',
        'project_code': '123',
        'moved_to_verify_win': '2017-11-12',
        'share_point_evidence': None,
    },))

    mocked_with_pm_assigned.return_value = iter(({
        'id': 2,
        'name': 'test',
        'project_code': '123',
        'project_manager_assigned_on': '2017-08-01',
        'project_manager_assigned_notification_on': '2017-11-12',
    },))

    mocked_with_proposal_deadline.return_value = iter(({
        'id': 1,
        'name': 'test',
        'project_code': '123',
        'proposal_deadline': '2018-02-05',
        'proposal_notification_on': '2018-02-20',
    },))

    mocked_by_actual_land_date.return_value = iter(({
        'id': 3,
        'name': 'test',
        'project_code': '123',
        'actual_land_date': '2019-04-30',
        'first_after_care_offered_on': '2019-04-30',
    },))

    report = generate_spi_report(1, 2017)

    assert [
        {
            'id': 2,
            'name': 'test',
            'project_code': '123',
            'email_received_date': None,
            'moved_to_active_on': '2017-10-11',
            'project_manager_assigned_on': '2017-08-01',
            'project_manager_assigned_notification_on': '2017-11-12'
        },
        {
            'id': 1,
            'name': 'test',
            'project_code': '123',
            'moved_to_verify_win': '2017-11-12',
            'share_point_evidence': None,
            'proposal_deadline': '2018-02-05',
            'proposal_notification_on': '2018-02-20'
        },
        {
            'id': 3,
            'name': 'test',
            'project_code': '123',
            'actual_land_date': '2019-04-30',
            'first_after_care_offered_on': '2019-04-30'
        }
    ] == [row for row in report]
