import pytest

from django.core.exceptions import ObjectDoesNotExist

from datahub.company.test.factories import AdvisorFactory, ContactFactory
from datahub.core import constants
from datahub.investment.test.factories import InvestmentProjectFactory

pytestmark = pytest.mark.django_db


def test_project_code_cdms():
    project = InvestmentProjectFactory(cdms_project_code='P-79661656')
    assert project.project_code == 'P-79661656'
    with pytest.raises(ObjectDoesNotExist):
        project.investmentprojectcode


def test_project_code_datahub():
    project = InvestmentProjectFactory()
    assert project.investmentprojectcode
    assert project.project_code == 'DHP-{:08d}'.format(
        project.investmentprojectcode.id
    )


def test_document_link_cdms():
    project = InvestmentProjectFactory(cdms_project_code='P-79661656')
    assert project.document_link == 'http://example/cdms/P-79661656/'


def test_document_link_datahub():
    project = InvestmentProjectFactory()
    assert project.document_link == 'http://example/dh/{}/'.format(
        project.project_code
    )


def test_project_manager_team_none():
    project = InvestmentProjectFactory()
    assert project.project_manager_team is None


def test_project_manager_team_valid():
    huk_team = constants.Team.healthcare_uk.value
    advisor = AdvisorFactory(dit_team_id=huk_team.id)
    project = InvestmentProjectFactory(project_manager_id=advisor.id)
    assert str(project.project_manager_team.id) == huk_team.id


def test_project_assurance_team_none():
    project = InvestmentProjectFactory()
    assert project.project_assurance_team is None


def test_project_assurance_team_valid():
    huk_team = constants.Team.healthcare_uk.value
    advisor = AdvisorFactory(dit_team_id=huk_team.id)
    project = InvestmentProjectFactory(project_assurance_advisor_id=advisor.id)
    assert str(project.project_assurance_team.id) == huk_team.id
