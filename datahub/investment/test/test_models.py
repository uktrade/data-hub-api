"""Tests for investment models."""

import pytest

from django.core.exceptions import ObjectDoesNotExist

from datahub.company.test.factories import AdviserFactory
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
