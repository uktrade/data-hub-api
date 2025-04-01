import logging
from unittest import mock

import pytest
from django.core.management import call_command

from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import InvestmentProjectFactory

pytestmark = pytest.mark.django_db


# TODO: Remove file once command has been run as one-off data modification


def test_set_site_address_is_company_address(caplog):
    # setup investment projects
    project_to_be_modified = InvestmentProjectFactory(
        site_address_is_company_address=None,
        site_decided=True,
    )
    InvestmentProjectFactory(
        site_address_is_company_address=None,
        site_decided=False,
    )
    InvestmentProjectFactory(
        site_address_is_company_address=None,
        site_decided=None,
    )
    InvestmentProjectFactory(site_address_is_company_address=True)
    InvestmentProjectFactory(site_address_is_company_address=False)

    # initial assertions
    assert project_to_be_modified.site_address_is_company_address is None
    assert InvestmentProject.objects.count() == 5
    assert InvestmentProject.objects.filter(site_address_is_company_address=None).count() == 3
    assert InvestmentProject.objects.filter(site_address_is_company_address=True).count() == 1
    assert InvestmentProject.objects.filter(site_address_is_company_address=False).count() == 1

    # execute job
    with caplog.at_level(logging.INFO):
        call_command('set_site_address_is_company_address')
        assert (
            'Found 1 projects with '
            'site_address_is_company_address == None and site_decided == True. '
            'Modifying...'
        ) in caplog.text
        assert 'Set site_address_is_company_address to False on 1 projects.' in caplog.text

    # final assertions
    project_to_be_modified.refresh_from_db()
    assert project_to_be_modified.site_address_is_company_address is False
    assert InvestmentProject.objects.count() == 5
    assert InvestmentProject.objects.filter(site_address_is_company_address=None).count() == 2
    assert InvestmentProject.objects.filter(site_address_is_company_address=True).count() == 1
    assert InvestmentProject.objects.filter(site_address_is_company_address=False).count() == 2


def test_set_site_address_is_company_address_when_theres_no_projects(caplog):
    with caplog.at_level(logging.INFO):
        call_command('set_site_address_is_company_address')
        assert (
            'No projects with '
            'site_address_is_company_address == None and site_decided == True found. '
            'Exiting...'
        ) in caplog.text


def test_set_site_address_is_company_address_handles_error(caplog):
    with (
        mock.patch('datahub.investment.project.models.InvestmentProject.objects') as mock_objects,
        caplog.at_level(logging.ERROR),
    ):
        mock_objects.filter.side_effect = Exception('A mocked filtering error')
        call_command('set_site_address_is_company_address')
        assert (
            'An error occurred trying to set site_address_is_company_address '
            'value for existing projects'
        ) in caplog.text
