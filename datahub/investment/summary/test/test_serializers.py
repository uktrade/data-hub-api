from datetime import date

import pytest
from freezegun import freeze_time

from datahub.company.test.factories import AdviserFactory
from datahub.core.constants import InvestmentProjectStage
from datahub.investment.project.test.factories import (
    InvestmentProjectFactory,
    InvestmentProjectTeamMemberFactory,
)
from datahub.investment.summary.serializers import AdvisorIProjectSummarySerializer


@pytest.fixture
def adviser():
    """An adviser for testing."""
    return AdviserFactory()


@pytest.fixture
def projects(adviser):
    """
    A number of projects at different stages associated to an adviser.
    """
    # 4 Prospects with no dates set
    for _index in range(4):
        InvestmentProjectFactory(
            stage_id=InvestmentProjectStage.prospect.value.id,
            client_relationship_manager=adviser,
        )
    # 3 Assign PM in 2015-16
    for _index in range(3):
        InvestmentProjectFactory(
            stage_id=InvestmentProjectStage.assign_pm.value.id,
            project_assurance_adviser=adviser,
            estimated_land_date=date(2015, 5, 1),
        )
    # 2 Active in 2015-16
    for _index in range(2):
        project = InvestmentProjectFactory(
            stage_id=InvestmentProjectStage.active.value.id,
            project_manager=adviser,
            estimated_land_date=date(2015, 5, 1),
        )
        InvestmentProjectTeamMemberFactory(investment_project=project, adviser=adviser)
    # 1 Verify Win in 2014-15
    for _index in range(1):
        InvestmentProjectFactory(
            stage_id=InvestmentProjectStage.verify_win.value.id,
            project_manager=adviser,
            actual_land_date=date(2015, 1, 1),
        )
    # 2 Won in 2014-15
    for _index in range(2):
        InvestmentProjectFactory(
            stage_id=InvestmentProjectStage.won.value.id,
            client_relationship_manager=adviser,
            actual_land_date=date(2015, 1, 1),
        )


EXPECTED_ANNUAL_SUMMARIES = [
    {
        'financial_year': {
            'label': '2014-15',
            'start': date(2014, 4, 1),
            'end': date(2015, 3, 31),
        },
        'totals': {
            'prospect': 4,
            'assign_pm': 0,
            'active': 0,
            'verify_win': 1,
            'won': 2,
        },
    },
    {
        'financial_year': {
            'label': '2015-16',
            'start': date(2015, 4, 1),
            'end': date(2016, 3, 31),
        },
        'totals': {
            'prospect': 4,
            'assign_pm': 3,
            'active': 2,
            'verify_win': 0,
            'won': 0,
        },
    },
]


@pytest.mark.django_db()
@freeze_time('2015-04-01 12:30:00')
class TestAdvisorIProjectSummarySerializer:
    """
    Tests for the AdvisorIProjectSummarySerializer.
    """

    def test_annual_summaries(self, adviser, projects):
        """
        Annual Summaries should be given for the current and previous financial years.
        """
        serializer = AdvisorIProjectSummarySerializer(adviser)
        assert 'annual_summaries' in serializer.data
        assert serializer.data == {
            'adviser_id': str(adviser.id),
            'annual_summaries': EXPECTED_ANNUAL_SUMMARIES,
        }

    def test_annual_summaries_only_includes_advisers_projects(self, adviser, projects):
        """
        Annual Summaries should not include counts of projects from other advisers.
        """
        another_adviser = AdviserFactory()
        for _index in range(2):
            InvestmentProjectFactory(
                stage_id=InvestmentProjectStage.won.value.id,
                client_relationship_manager=another_adviser,
                actual_land_date=date(2015, 1, 1),
            )

        serializer = AdvisorIProjectSummarySerializer(adviser)
        assert 'annual_summaries' in serializer.data
        assert serializer.data == {
            'adviser_id': str(adviser.id),
            'annual_summaries': EXPECTED_ANNUAL_SUMMARIES,
        }
