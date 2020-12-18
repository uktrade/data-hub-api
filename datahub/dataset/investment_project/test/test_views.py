import pytest
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, TeamFactory
from datahub.core.constants import InvestmentProjectStage as InvestmentProjectStageConstant
from datahub.core.constants import Service as ServiceConstant
from datahub.core.test_utils import (
    format_date_or_datetime,
    get_attr_or_none,
    str_or_none,
)
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.interaction.test.factories import InvestmentProjectInteractionFactory
from datahub.investment.project.proposition.models import PropositionDocument
from datahub.investment.project.proposition.test.factories import PropositionFactory
from datahub.investment.project.test.factories import (
    ActiveInvestmentProjectFactory,
    AssignPMInvestmentProjectFactory,
    FDIInvestmentProjectFactory,
    InvestmentProjectFactory,
    InvestmentProjectTeamMemberFactory,
    VerifyWinInvestmentProjectFactory,
    WonInvestmentProjectFactory,
)
from datahub.metadata.models import Team

pytestmark = pytest.mark.django_db


@pytest.fixture
def ist_adviser():
    """Provides IST adviser."""
    team = TeamFactory(tags=[Team.Tag.INVESTMENT_SERVICES_TEAM])
    yield AdviserFactory(dit_team_id=team.id)


@pytest.fixture
def propositions(ist_adviser):
    """Gets variety of propositions."""
    investment_project = InvestmentProjectFactory(
        project_manager=ist_adviser,
    )
    adviser = AdviserFactory(
        first_name='John',
        last_name='Doe',
    )
    items = [
        PropositionFactory(
            deadline='2017-01-05',
            status='ongoing',
            adviser=adviser,
            investment_project=investment_project,
            created_by=ist_adviser,
        ),
        PropositionFactory(
            deadline='2017-01-05',
            status='ongoing',
            adviser=adviser,
            investment_project=investment_project,
            created_by=ist_adviser,
        ),
        PropositionFactory(
            deadline='2017-01-05',
            status='ongoing',
            adviser=adviser,
            investment_project=investment_project,
            created_by=ist_adviser,
        ),
    ]

    with freeze_time('2017-01-04 11:11:11'):
        entity_document = PropositionDocument.objects.create(
            proposition_id=items[1].pk,
            original_filename='test.txt',
            created_by=adviser,
        )
        entity_document.document.mark_as_scanned(True, '')
        items[1].complete(by=adviser, details='what')

        items[2].abandon(by=adviser, details='what')

    yield items


def get_expected_data_from_project(project, won_date=None):
    """Returns expected dictionary based on given project"""
    return {
        'actual_land_date': format_date_or_datetime(project.actual_land_date),
        'actual_uk_region_names': (
            [region.name for region in project.actual_uk_regions.order_by('name')]
        ) if project.actual_uk_regions.exists() else None,
        'address_1': project.address_1,
        'address_2': project.address_2,
        'address_town': project.address_town,
        'address_postcode': project.address_postcode,
        'anonymous_description': project.anonymous_description,
        'associated_non_fdi_r_and_d_project_id': str_or_none(
            project.associated_non_fdi_r_and_d_project_id,
        ),
        'average_salary__name': get_attr_or_none(project, 'average_salary.name'),
        'business_activity_names': (
            [activity.name for activity in project.business_activities.order_by('name')]
        ) if project.business_activities.exists() else None,
        'client_relationship_manager_id': str_or_none(project.client_relationship_manager_id),
        'client_requirements': project.client_requirements,
        'competing_countries': (
            [country.name for country in project.competitor_countries.order_by('name')]
            if project.competitor_countries.exists() else [None]
        ),
        'country_investment_originates_from_id': str_or_none(
            project.country_investment_originates_from_id,
        ),
        'country_investment_originates_from__name': get_attr_or_none(
            project,
            'country_investment_originates_from.name',
        ),
        'created_by_id': str_or_none(project.created_by_id),
        'created_on': format_date_or_datetime(project.created_on),
        'delivery_partner_names': (
            [partner.name for partner in project.delivery_partners.order_by('name')]

        ) if project.delivery_partners.exists() else None,
        'description': project.description,
        'estimated_land_date': format_date_or_datetime(project.estimated_land_date),
        'export_revenue': project.export_revenue,
        'fdi_type__name': get_attr_or_none(project, 'fdi_type.name'),
        'fdi_value__name': get_attr_or_none(project, 'fdi_value.name'),
        'foreign_equity_investment': (
            float(project.foreign_equity_investment)
            if project.foreign_equity_investment
            else None
        ),
        'government_assistance': project.government_assistance,
        'gross_value_added': project.gross_value_added,
        'gva_multiplier__multiplier': (
            float(get_attr_or_none(project, 'gva_multiplier.multiplier'))
            if get_attr_or_none(project, 'gva_multiplier.multiplier')
            else None
        ),
        'id': str(project.pk),
        'investment_type__name': get_attr_or_none(project, 'investment_type.name'),
        'investor_company_id': str_or_none(project.investor_company_id),
        'investor_company_sector': get_attr_or_none(
            project,
            'investor_company.sector.name',
        ),
        'investor_type__name': get_attr_or_none(project, 'investor_type.name'),
        'level_of_involvement_name': get_attr_or_none(project, 'level_of_involvement.name'),
        'likelihood_to_land__name': get_attr_or_none(project, 'likelihood_to_land.name'),
        'modified_by_id': str_or_none(project.modified_by_id),
        'modified_on': format_date_or_datetime(project.modified_on),
        'name': project.name,
        'new_tech_to_uk': project.new_tech_to_uk,
        'non_fdi_r_and_d_budget': project.non_fdi_r_and_d_budget,
        'number_new_jobs': project.number_new_jobs,
        'number_safeguarded_jobs': project.number_safeguarded_jobs,
        'other_business_activity': project.other_business_activity,
        'project_arrived_in_triage_on': format_date_or_datetime(
            project.project_arrived_in_triage_on),
        'project_assurance_adviser_id': str_or_none(project.project_assurance_adviser_id),
        'project_first_moved_to_won': won_date,
        'project_manager_id': str_or_none(project.project_manager_id),
        'project_reference': project.project_code,
        'proposal_deadline': format_date_or_datetime(project.proposal_deadline),
        'r_and_d_budget': project.r_and_d_budget,
        'referral_source_activity__name': get_attr_or_none(
            project,
            'referral_source_activity.name',
        ),
        'referral_source_activity_marketing__name': get_attr_or_none(
            project,
            'referral_source_activity_marketing.name',
        ),
        'referral_source_activity_website__name': get_attr_or_none(
            project,
            'referral_source_activity_website.name',
        ),
        'sector_name': get_attr_or_none(project, 'sector.name'),
        'specific_programme__name': get_attr_or_none(project, 'specific_programme.name'),
        'stage__name': get_attr_or_none(project, 'stage.name'),
        'status': project.status,
        'strategic_driver_names': (
            [driver.name for driver in project.strategic_drivers.order_by('name')]
        ) if project.strategic_drivers.exists() else None,
        'team_member_ids': (
            [
                str(team_member.adviser_id)
                for team_member in project.team_members.order_by('id')
            ]
        ) if project.team_members.exists() else [None],
        'total_investment': float(project.total_investment) if project.total_investment else None,
        'uk_company_id': str_or_none(project.uk_company_id),
        'uk_company_sector': get_attr_or_none(project, 'uk_company.sector.name'),
        'uk_region_location_names': (
            [region.name for region in project.uk_region_locations.order_by('name')]
        ) if project.uk_region_locations.exists() else None,
    }


@pytest.mark.django_db
class TestInvestmentProjectsDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for InvestmentProjectsDatasetView
    """

    view_url = reverse('api-v4:dataset:investment-projects-dataset')
    factory = InvestmentProjectFactory

    @pytest.mark.parametrize(
        'project_factory,won_date',
        (
            (InvestmentProjectFactory, None),
            (FDIInvestmentProjectFactory, None),
            (AssignPMInvestmentProjectFactory, None),
            (ActiveInvestmentProjectFactory, None),
            (VerifyWinInvestmentProjectFactory, None),
            (WonInvestmentProjectFactory, '2017-01-01T00:00:00Z'),
        ),
    )
    def test_success(self, data_flow_api_client, project_factory, won_date):
        """Test that endpoint returns with expected data for a single project"""
        with freeze_time('2017-01-01 00:00:00'):
            project = project_factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_project(
            project,
            won_date=won_date,
        )
        assert result == expected_result

    def test_with_team_members(self, data_flow_api_client):
        """Test that endpoint returns with expected data for a single project with team members"""
        project = InvestmentProjectTeamMemberFactory().investment_project
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_project(project)
        assert result == expected_result

    def test_with_multiple_projects(self, data_flow_api_client):
        """Test that endpoint returns correct number of record in expected response"""
        with freeze_time('2019-01-01 12:30:00'):
            project_1 = InvestmentProjectFactory()
        with freeze_time('2019-01-03 12:00:00'):
            project_2 = InvestmentProjectFactory()
        with freeze_time('2019-01-01 12:00:00'):
            project_3 = InvestmentProjectFactory()
            project_4 = InvestmentProjectFactory()

        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_project_list = sorted([project_3, project_4],
                                       key=lambda item: item.pk) + [project_1, project_2]
        for index, project in enumerate(expected_project_list):
            assert str(project.id) == response_results[index]['id']


class TestInvestmentProjectsActivityDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for InvestmentProjectsActivityDatasetView

    It only tests if results are being returned. The results are validated in separate tests
    in the investment project app.
    """

    view_url = reverse('api-v4:dataset:investment-projects-activity-dataset')
    factory = InvestmentProjectFactory

    def test_propositions_are_being_formatted(self, data_flow_api_client, propositions):
        """Test that returned propositions are being formatted correctly."""
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK

        response_results = response.json()['results']
        assert len(response_results[0]['propositions']) == len(propositions)

        adviser_id = str(propositions[0].adviser_id)
        assert response_results == [
            {
                'propositions': [
                    {
                        'deadline': '2017-01-05',
                        'status': 'ongoing',
                        'modified_on': '',
                        'adviser_id': adviser_id,
                    },
                    {
                        'deadline': '2017-01-05',
                        'status': 'completed',
                        'modified_on': '2017-01-04T11:11:11+00:00',
                        'adviser_id': adviser_id,
                    },
                    {
                        'deadline': '2017-01-05',
                        'status': 'abandoned',
                        'modified_on': '2017-01-04T11:11:11+00:00',
                        'adviser_id': adviser_id,
                    },
                ],
                'investment_project_id': str(propositions[0].investment_project.id),
                'enquiry_processed': '',
                'enquiry_type': '',
                'enquiry_processed_by_id': '',
                'assigned_to_ist': '',
                'project_manager_assigned': '',
                'project_manager_assigned_by_id': '',
                'project_moved_to_won': '',
                'aftercare_offered_on': '',
            },
        ]

    def test_spi_fields_are_serialised(self, data_flow_api_client, ist_adviser):
        """Test that SPI fields are serialised."""
        pm_assigned_by = AdviserFactory()
        pm_assigned_on = now()
        investment_project = VerifyWinInvestmentProjectFactory(
            project_manager=ist_adviser,
            project_manager_first_assigned_on=pm_assigned_on,
            project_manager_first_assigned_by=pm_assigned_by,
        )
        spi1 = InvestmentProjectInteractionFactory(
            investment_project=investment_project,
            service_id=ServiceConstant.investment_enquiry_requested_more_information.value.id,
        )
        spi2 = InvestmentProjectInteractionFactory(
            investment_project=investment_project,
            service_id=ServiceConstant.investment_enquiry_assigned_to_ist_cmc.value.id,
        )
        with freeze_time('2017-01-01'):
            investment_project.stage_id = InvestmentProjectStageConstant.won.value.id
            investment_project.save()

        spi5 = InvestmentProjectInteractionFactory(
            investment_project=investment_project,
            service_id=ServiceConstant.investment_ist_aftercare_offered.value.id,
        )

        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK

        response_results = response.json()['results']
        assert response_results == [
            {
                'enquiry_processed': spi1.created_on.isoformat(),
                'enquiry_type': spi1.service.name,
                'enquiry_processed_by_id': str(spi1.created_by.id),
                'assigned_to_ist': spi2.created_on.isoformat(),
                'project_manager_assigned': pm_assigned_on.isoformat(),
                'project_manager_assigned_by_id': str(pm_assigned_by.id),
                'investment_project_id': str(investment_project.id),
                'project_moved_to_won': '2017-01-01T00:00:00+00:00',
                'aftercare_offered_on': spi5.created_on.isoformat(),
                'propositions': [],
            },
        ]
