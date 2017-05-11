"""Tests for investment models."""

import pytest

from django.core.exceptions import ObjectDoesNotExist

from datahub.company.test.factories import AdvisorFactory
from datahub.core import constants
from datahub.investment.test.factories import InvestmentProjectFactory

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
    assert project.project_code == 'DHP-{:08d}'.format(
        project.investmentprojectcode.id
    )


def test_project_manager_team_none():
    """Tests project_manager_team for a project without a project manager."""
    project = InvestmentProjectFactory()
    assert project.project_manager_team is None


def test_project_manager_team_valid():
    """Tests project_manager_team for a project with a project manager."""
    huk_team = constants.Team.healthcare_uk.value
    advisor = AdvisorFactory(dit_team_id=huk_team.id)
    project = InvestmentProjectFactory(project_manager_id=advisor.id)
    assert str(project.project_manager_team.id) == huk_team.id


def test_project_assurance_team_none():
    """Tests project_assurance_team for a project w/o an assurance advisor."""
    project = InvestmentProjectFactory()
    assert project.project_assurance_team is None


def test_project_assurance_team_valid():
    """Tests project_assurance_team for a project w/ an assurance advisor."""
    huk_team = constants.Team.healthcare_uk.value
    advisor = AdvisorFactory(dit_team_id=huk_team.id)
    project = InvestmentProjectFactory(project_assurance_advisor_id=advisor.id)
    assert str(project.project_assurance_team.id) == huk_team.id
