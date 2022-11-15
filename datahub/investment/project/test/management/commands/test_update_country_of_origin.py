import logging

import pytest
from reversion.models import Version

from datahub.investment.project.management.commands import update_country_of_origin
from datahub.investment.project.test.factories import InvestmentProjectFactory

pytestmark = pytest.mark.django_db


class TestUpdateCountryOfOriginCommand:
    """Test update country of origin command."""

    def test_update_country_of_origin(self, caplog):
        """Test populating country of origin."""
        caplog.set_level(logging.INFO)
        projects = InvestmentProjectFactory.create_batch(
            2,
            country_investment_originates_from=None,
        )
        control_projects = [
            # investment project with country of origin already set
            InvestmentProjectFactory(),
            # investment project without investor company (edge case)
            InvestmentProjectFactory(
                investor_company=None,
                country_investment_originates_from=None,
            ),
        ]

        for project in projects:
            assert project.country_investment_originates_from is None
            assert project.investor_company.address_country

        assert (
            control_projects[0].country_investment_originates_from
            == control_projects[0].investor_company.address_country
        )
        assert control_projects[1].investor_company is None

        self._run_command()

        for project in projects:
            project.refresh_from_db()
            assert (
                project.country_investment_originates_from
                == project.investor_company.address_country
            )
            versions = Version.objects.get_for_object(project)
            assert versions.count() == 1
            assert versions[0].revision.get_comment() == 'Automated country of origin update.'

        # check that no updates have been made to control investment project that already has
        # country of origin set or does not have investor company set
        for control_project in control_projects:
            versions = Version.objects.get_for_object(control_project)
            assert versions.count() == 0

        assert any(
            'schedule_update_country_of_origin_for_investment_projects'
            in message for message in caplog.messages
        )
        assert any(
            'Task update_country_of_origin_for_investment_projects completed'
            in message for message in caplog.messages
        )

    def _run_command(self):
        cmd = update_country_of_origin.Command()
        cmd.handle()
