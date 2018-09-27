"""Tests for investment models."""

from datetime import datetime
from uuid import UUID

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import utc
from freezegun import freeze_time

from datahub.company.test.factories import AdviserFactory
from datahub.core import constants
from datahub.investment.test.factories import (
    InvestmentProjectFactory, InvestmentProjectTeamMemberFactory,
)

pytestmark = pytest.mark.django_db


def test_project_code_cdms():
    """Tests that correct project codes are generated for CDMS projects."""
    project = InvestmentProjectFactory(cdms_project_code='P-79661656')
    assert project.project_code == 'P-79661656'
    with pytest.raises(ObjectDoesNotExist):
        project.investmentprojectcode


def test_project_code_datahub():
    """Tests that correct project codes are generated for Data Hub projects."""
    project = InvestmentProjectFactory()
    assert project.investmentprojectcode
    project_num = project.investmentprojectcode.id
    assert project.project_code == f'DHP-{project_num:08d}'


def test_no_project_code():
    """Tests that None is returned when a project code is not set."""
    # cdms_project_code is set and removed to avoid a DH project code
    # being generated
    project = InvestmentProjectFactory(cdms_project_code='P-79661656')
    project.cdms_project_code = None
    assert project.project_code is None


def test_client_relationship_manager_team_none():
    """
    Tests client_relationship_manager_team for a project without a client relationship
    manager.
    """
    project = InvestmentProjectFactory(client_relationship_manager=None)
    assert project.client_relationship_manager_team is None


def test_client_relationship_manager_team_valid():
    """
    Tests client_relationship_manager_team for a project with a client relationship
    manager.
    """
    project = InvestmentProjectFactory()
    assert project.client_relationship_manager_team


def test_investor_company_country_none():
    """
    Tests client_relationship_manager_team for a project without a client relationship
    manager.
    """
    project = InvestmentProjectFactory(investor_company=None)
    assert project.investor_company_country is None


def test_investor_company_country_valid():
    """
    Tests client_relationship_manager_team for a project with a client relationship
    manager.
    """
    project = InvestmentProjectFactory()
    assert project.investor_company_country


def test_project_manager_team_none():
    """Tests project_manager_team for a project without a project manager."""
    project = InvestmentProjectFactory()
    assert project.project_manager_team is None


def test_project_manager_team_valid():
    """Tests project_manager_team for a project with a project manager."""
    huk_team = constants.Team.healthcare_uk.value
    adviser = AdviserFactory(dit_team_id=huk_team.id)
    project = InvestmentProjectFactory(project_manager_id=adviser.id)
    assert str(project.project_manager_team.id) == huk_team.id


def test_project_assurance_team_none():
    """Tests project_assurance_team for a project w/o an assurance adviser."""
    project = InvestmentProjectFactory()
    assert project.project_assurance_team is None


def test_project_assurance_team_valid():
    """Tests project_assurance_team for a project w/ an assurance adviser."""
    huk_team = constants.Team.healthcare_uk.value
    adviser = AdviserFactory(dit_team_id=huk_team.id)
    project = InvestmentProjectFactory(project_assurance_adviser_id=adviser.id)
    assert str(project.project_assurance_team.id) == huk_team.id


@pytest.mark.parametrize(
    'field',
    (
        'client_relationship_manager',
        'project_assurance_adviser',
        'project_manager',
        'created_by',
    ),
)
def test_associated_advisers_specific_roles(field):
    """Tests that get_associated_advisers() includes advisers in specific roles."""
    adviser = AdviserFactory()
    factory_kwargs = {
        field: adviser,
    }
    project = InvestmentProjectFactory(**factory_kwargs)
    assert adviser in tuple(project.get_associated_advisers())


def test_associated_advisers_team_members():
    """Tests that get_associated_advisers() includes team members."""
    adviser = AdviserFactory()
    project = InvestmentProjectFactory()
    InvestmentProjectTeamMemberFactory(investment_project=project, adviser=adviser)
    assert adviser in tuple(project.get_associated_advisers())


def test_associated_advisers_no_none():
    """Tests that get_associated_advisers() does not include None."""
    project = InvestmentProjectFactory(client_relationship_manager_id=None)
    assert None not in tuple(project.get_associated_advisers())


def test_creates_stage_log_if_stage_was_modified():
    """Tests that change to investment project stage creates a stage log record."""
    dates = (
        datetime(2017, 4, 28, 17, 35, tzinfo=utc),
        datetime(2017, 4, 28, 17, 37, tzinfo=utc),
    )
    date_iter = iter(dates)

    with freeze_time(next(date_iter)):
        project = InvestmentProjectFactory()
    with freeze_time(next(date_iter)):
        project.stage_id = constants.InvestmentProjectStage.assign_pm.value.id
        project.save()

    date_iter = iter(dates)
    assert [
        (entry.stage.id, entry.created_on) for entry in project.stage_log.order_by('created_on')
    ] == [
        (UUID(constants.InvestmentProjectStage.prospect.value.id), next(date_iter)),
        (UUID(constants.InvestmentProjectStage.assign_pm.value.id), next(date_iter)),
    ]


def test_doesnt_create_stage_log_if_stage_was_not_modified():
    """Tests that stage log is not created when there is no change to stage."""
    project = InvestmentProjectFactory()
    # no change to the stage
    project.save()
    assert project.stage_log.count() == 1


@freeze_time(datetime(2017, 4, 28, 17, 35, tzinfo=utc))
def test_stage_log_added_when_investment_project_is_created():
    """Tests that stage is being logged when Investment Projects is created."""
    project = InvestmentProjectFactory()
    assert [
        (entry.stage.id, entry.created_on) for entry in project.stage_log.all()
    ] == [
        (
            UUID(constants.InvestmentProjectStage.prospect.value.id),
            datetime(2017, 4, 28, 17, 35, tzinfo=utc),
        ),
    ]
