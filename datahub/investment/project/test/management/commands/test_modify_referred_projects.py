import logging

import pytest

from django.core.management import call_command

from datahub.investment.project.constants import SpecificProgramme as SpecificProgrammeConstants
from datahub.investment.project.models import (
    InvestmentProject,
    SpecificProgramme,
)
from datahub.investment.project.test.factories import InvestmentProjectFactory


REFERRED_TO_EYB_PROGRAMME_ID = SpecificProgrammeConstants.referred_to_eyb.value.id
REFERRED_STATUS_VALUE = InvestmentProject.Status.REFERRED.value
ONGOING_STATUS_VALUE = InvestmentProject.Status.ONGOING.value
DELAYED_STATUS_VALUE = InvestmentProject.Status.DELAYED.value


pytestmark = pytest.mark.django_db


# TODO: Remove file once command has been run as one-off data modification


def test_modify_referred_projects(caplog):
    referred_to_eyb_programme = SpecificProgramme.objects.get(
        pk=REFERRED_TO_EYB_PROGRAMME_ID,
    )

    # setup investment projects
    referred_project = InvestmentProjectFactory(
        status=REFERRED_STATUS_VALUE,
        specific_programmes=[],
    )
    other_referred_project = InvestmentProjectFactory(
        status=REFERRED_STATUS_VALUE,
        specific_programmes=[referred_to_eyb_programme],
    )
    InvestmentProjectFactory(
        status=ONGOING_STATUS_VALUE,
        specific_programmes=[],
    )
    InvestmentProjectFactory(
        status=DELAYED_STATUS_VALUE,
        specific_programmes=[],
    )

    # initial assertions
    assert InvestmentProject.objects.count() == 4

    assert referred_project.status == REFERRED_STATUS_VALUE
    assert referred_project.specific_programmes.count() == 0

    assert other_referred_project.status == REFERRED_STATUS_VALUE
    assert other_referred_project.specific_programmes.count() == 1
    assert referred_to_eyb_programme in other_referred_project.specific_programmes.all()

    # execute job
    with caplog.at_level(logging.INFO):
        call_command('modify_referred_projects')
        assert 'Found 2 referred projects. Modifying...' in caplog.text
        assert 'Finished modifying referred projects.' in caplog.text

    # final assertions
    referred_project.refresh_from_db()
    assert referred_project.status == ONGOING_STATUS_VALUE
    assert referred_project.specific_programmes.count() == 1
    assert referred_to_eyb_programme in referred_project.specific_programmes.all()

    other_referred_project.refresh_from_db()
    assert other_referred_project.status == ONGOING_STATUS_VALUE
    assert other_referred_project.specific_programmes.count() == 1

    assert InvestmentProject.objects.count() == 4
    assert InvestmentProject.objects.filter(status=ONGOING_STATUS_VALUE).count() == 3
    assert InvestmentProject.objects.filter(
        specific_programmes=REFERRED_TO_EYB_PROGRAMME_ID,
    ).count() == 2


def test_modify_referred_projects_when_theres_no_projects(caplog):
    with caplog.at_level(logging.INFO):
        call_command('modify_referred_projects')
        assert 'No referred projects found. Exiting...' in caplog.text


def test_modify_referred_projects_handles_error(caplog):
    # cause error by deleting the Referred to EYB specific programme
    SpecificProgramme.objects.get(
        pk=REFERRED_TO_EYB_PROGRAMME_ID,
    ).delete()
    with caplog.at_level(logging.ERROR):
        call_command('modify_referred_projects')
        assert 'An error occurred trying to modify referred projects' in caplog.text
