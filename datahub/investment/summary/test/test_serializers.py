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
from datahub.metadata.models import InvestmentProjectStage as InvestmentProjectStageModel


@pytest.fixture
def adviser():
    """An adviser for testing."""
    return AdviserFactory()


@pytest.fixture
def prospect_projects(adviser):
    """Mock prospect projects"""
    # 5 Prospects created in 2014-15
    with freeze_time('2015-03-31 12:30:00'):
        for _index in range(5):
            InvestmentProjectFactory(
                stage_id=InvestmentProjectStage.prospect.value.id,
                client_relationship_manager=adviser,
                estimated_land_date=date(2016, 4, 1),
            )
    # 6 Prospects created in 2015-16
    with freeze_time('2015-04-01 12:30:00'):
        for _index in range(6):
            InvestmentProjectFactory(
                stage_id=InvestmentProjectStage.prospect.value.id,
                client_relationship_manager=adviser,
                estimated_land_date=date(2015, 5, 1),
            )


@pytest.fixture
def assign_pm_projects(adviser):
    """Mock assign pm projects"""
    # 1 Assign PM in 2016-17
    for _index in range(1):
        InvestmentProjectFactory(
            stage_id=InvestmentProjectStage.assign_pm.value.id,
            project_assurance_adviser=adviser,
            estimated_land_date=date(2017, 3, 1),
        )
    # 3 Assign PM in 2015-16
    for _index in range(3):
        InvestmentProjectFactory(
            stage_id=InvestmentProjectStage.assign_pm.value.id,
            project_assurance_adviser=adviser,
            estimated_land_date=date(2015, 4, 1),
        )


@pytest.fixture
def active_projects(adviser):
    """Mock active projects"""
    # 3 Active for 2016-17
    for _index in range(3):
        project = InvestmentProjectFactory(
            stage_id=InvestmentProjectStage.active.value.id,
            estimated_land_date=date(2016, 4, 1),
        )
        InvestmentProjectTeamMemberFactory(investment_project=project, adviser=adviser)
    # 2 Active in 2015-16
    for _index in range(2):
        project = InvestmentProjectFactory(
            stage_id=InvestmentProjectStage.active.value.id,
            estimated_land_date=date(2015, 5, 1),
        )
        InvestmentProjectTeamMemberFactory(investment_project=project, adviser=adviser)


@pytest.fixture
def verify_win_projects(adviser):
    """Mock verify win projects"""
    # 1 Verify Win in 2014-15
    for _index in range(1):
        InvestmentProjectFactory(
            stage_id=InvestmentProjectStage.verify_win.value.id,
            project_manager=adviser,
            actual_land_date=date(2015, 3, 31),
        )
    # 3 Verify Win in 2015-16
    for _index in range(3):
        InvestmentProjectFactory(
            stage_id=InvestmentProjectStage.verify_win.value.id,
            project_manager=adviser,
            actual_land_date=date(2016, 3, 31),
        )


@pytest.fixture
def won_projects(adviser):
    """Mock won projects"""
    # 2 Won in 2014-15
    for _index in range(2):
        InvestmentProjectFactory(
            stage_id=InvestmentProjectStage.won.value.id,
            client_relationship_manager=adviser,
            actual_land_date=date(2015, 1, 1),
        )
    # 1 Won in 2013-14
    for _index in range(1):
        InvestmentProjectFactory(
            stage_id=InvestmentProjectStage.won.value.id,
            client_relationship_manager=adviser,
            actual_land_date=date(2014, 1, 1),
        )


@pytest.fixture
def projects(
    prospect_projects,
    assign_pm_projects,
    active_projects,
    verify_win_projects,
    won_projects,
):
    """A number of projects at different stages associated to an adviser."""
    pass


EXPECTED_ANNUAL_SUMMARIES = [
    {
        'financial_year': {
            'label': '2016-17',
            'start': date(2016, 4, 1),
            'end': date(2017, 3, 31),
        },
        'totals': {
            'prospect': {
                'label': 'Prospect',
                'id': InvestmentProjectStage.prospect.value.id,
                'value': 11,
            },
            'assign_pm': {
                'label': 'Assign PM',
                'id': InvestmentProjectStage.assign_pm.value.id,
                'value': 1,
            },
            'active': {
                'label': 'Active',
                'id': InvestmentProjectStage.active.value.id,
                'value': 3,
            },
            'verify_win': {
                'label': 'Verify Win',
                'id': InvestmentProjectStage.verify_win.value.id,
                'value': 0,
            },
            'won': {
                'label': 'Won',
                'id': InvestmentProjectStage.won.value.id,
                'value': 0,
            },
        },
    },
    {
        'financial_year': {
            'label': '2015-16',
            'start': date(2015, 4, 1),
            'end': date(2016, 3, 31),
        },
        'totals': {
            'prospect': {
                'label': 'Prospect',
                'id': InvestmentProjectStage.prospect.value.id,
                'value': 11,
            },
            'assign_pm': {
                'label': 'Assign PM',
                'id': InvestmentProjectStage.assign_pm.value.id,
                'value': 3,
            },
            'active': {
                'label': 'Active',
                'id': InvestmentProjectStage.active.value.id,
                'value': 2,
            },
            'verify_win': {
                'label': 'Verify Win',
                'id': InvestmentProjectStage.verify_win.value.id,
                'value': 3,
            },
            'won': {
                'label': 'Won',
                'id': InvestmentProjectStage.won.value.id,
                'value': 0,
            },
        },
    },
    {
        'financial_year': {
            'label': '2014-15',
            'start': date(2014, 4, 1),
            'end': date(2015, 3, 31),
        },
        'totals': {
            'prospect': {
                'label': 'Prospect',
                'id': InvestmentProjectStage.prospect.value.id,
                'value': 5,
            },
            'assign_pm': {
                'label': 'Assign PM',
                'id': InvestmentProjectStage.assign_pm.value.id,
                'value': 0,
            },
            'active': {
                'label': 'Active',
                'id': InvestmentProjectStage.active.value.id,
                'value': 0,
            },
            'verify_win': {
                'label': 'Verify Win',
                'id': InvestmentProjectStage.verify_win.value.id,
                'value': 1,
            },
            'won': {
                'label': 'Won',
                'id': InvestmentProjectStage.won.value.id,
                'value': 2,
            },
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

    def test_annual_summaries_include_team_member_projects(self, adviser):
        """
        Annual summaries should include counts of projects where adviser is a
        team member
        """
        for _index in range(2):
            project = InvestmentProjectFactory(
                stage_id=InvestmentProjectStage.active.value.id,
                actual_land_date=date(2015, 1, 1),
            )
            InvestmentProjectTeamMemberFactory(
                investment_project=project,
                adviser=adviser,
            )

        serializer = AdvisorIProjectSummarySerializer(adviser)
        assert serializer.data['annual_summaries'][2]['totals']['active']['value'] == 2

    def test_annual_summaries_only_count_team_members_once(self, adviser):
        """
        When an adviser is assigned multiple roles on a project, that project
        should only be counted once in the summary.
        """
        project = InvestmentProjectFactory(
            stage_id=InvestmentProjectStage.active.value.id,
            project_manager=adviser,
            estimated_land_date=date(2014, 5, 1),
        )
        InvestmentProjectTeamMemberFactory(
            investment_project=project,
            adviser=adviser,
        )
        InvestmentProjectTeamMemberFactory(
            investment_project=project,
            adviser=AdviserFactory(),
        )

        serializer = AdvisorIProjectSummarySerializer(adviser)
        assert serializer.data['annual_summaries'][2]['totals']['active']['value'] == 1

    def test_unexpected_stage_is_not_included(self, adviser, projects):
        """
        Annual Summaries should ignore unexpected stages.
        """
        bad_stage = InvestmentProjectStageModel.objects.create(name='Bad Stage')
        for _index in range(2):
            InvestmentProjectFactory(
                stage_id=bad_stage.id,
                client_relationship_manager=adviser,
                actual_land_date=date(2015, 1, 1),
            )

        serializer = AdvisorIProjectSummarySerializer(adviser)
        assert 'annual_summaries' in serializer.data
        assert serializer.data == {
            'adviser_id': str(adviser.id),
            'annual_summaries': EXPECTED_ANNUAL_SUMMARIES,
        }

    def test_actual_land_date_takes_precedence_over_estimated(self, adviser):
        """
        Test that the actual land date is used if it exists.
        """
        # 2 wins estimated in 2014-15, but actually landed in 2015-16
        for _index in range(2):
            InvestmentProjectFactory(
                stage_id=InvestmentProjectStage.won.value.id,
                client_relationship_manager=adviser,
                actual_land_date=date(2016, 1, 1),
                estimated_land_date=date(2015, 1, 1),
            )

        serializer = AdvisorIProjectSummarySerializer(adviser)

        assert 'annual_summaries' in serializer.data
        assert len(serializer.data['annual_summaries']) == 3
        next_summary, current_summary, previous_summary = serializer.data['annual_summaries']
        assert previous_summary['financial_year']['label'] == '2014-15'
        assert previous_summary['totals']['won']['value'] == 0
        assert current_summary['financial_year']['label'] == '2015-16'
        assert current_summary['totals']['won']['value'] == 2
        assert next_summary['financial_year']['label'] == '2016-17'
        assert next_summary['totals']['won']['value'] == 0

    def test_financial_year_edges(self, adviser):
        """
        31 March should fall in the previous financial year and 1 April in the current.
        """
        # 2 active on 1 April 2015 (2015-16 financial year)
        for _index in range(2):
            InvestmentProjectFactory(
                stage_id=InvestmentProjectStage.active.value.id,
                client_relationship_manager=adviser,
                actual_land_date=date(2015, 4, 1),
            )
        # 3 won on 31 March 2015 (2014-15 financial year)
        for _index in range(3):
            InvestmentProjectFactory(
                stage_id=InvestmentProjectStage.won.value.id,
                client_relationship_manager=adviser,
                actual_land_date=date(2015, 3, 31),
            )

        serializer = AdvisorIProjectSummarySerializer(adviser)

        assert 'annual_summaries' in serializer.data
        assert len(serializer.data['annual_summaries']) == 3
        assert serializer.data['annual_summaries'][1:3] == [
            {
                'financial_year': {
                    'label': '2015-16',
                    'start': date(2015, 4, 1),
                    'end': date(2016, 3, 31),
                },
                'totals': {
                    'prospect': {
                        'label': 'Prospect',
                        'id': InvestmentProjectStage.prospect.value.id,
                        'value': 0,
                    },
                    'assign_pm': {
                        'label': 'Assign PM',
                        'id': InvestmentProjectStage.assign_pm.value.id,
                        'value': 0,
                    },
                    'active': {
                        'label': 'Active',
                        'id': InvestmentProjectStage.active.value.id,
                        'value': 2,
                    },
                    'verify_win': {
                        'label': 'Verify Win',
                        'id': InvestmentProjectStage.verify_win.value.id,
                        'value': 0,
                    },
                    'won': {
                        'label': 'Won',
                        'id': InvestmentProjectStage.won.value.id,
                        'value': 0,
                    },
                },
            },
            {
                'financial_year': {
                    'label': '2014-15',
                    'start': date(2014, 4, 1),
                    'end': date(2015, 3, 31),
                },
                'totals': {
                    'prospect': {
                        'label': 'Prospect',
                        'id': InvestmentProjectStage.prospect.value.id,
                        'value': 0,
                    },
                    'assign_pm': {
                        'label': 'Assign PM',
                        'id': InvestmentProjectStage.assign_pm.value.id,
                        'value': 0,
                    },
                    'active': {
                        'label': 'Active',
                        'id': InvestmentProjectStage.active.value.id,
                        'value': 0,
                    },
                    'verify_win': {
                        'label': 'Verify Win',
                        'id': InvestmentProjectStage.verify_win.value.id,
                        'value': 0,
                    },
                    'won': {
                        'label': 'Won',
                        'id': InvestmentProjectStage.won.value.id,
                        'value': 3,
                    },
                },
            },
        ]
