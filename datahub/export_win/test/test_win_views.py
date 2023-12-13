import pytest

from django.utils.timezone import now

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    ContactFactory,
)
from datahub.core.constants import (
    AssociatedProgramme as AssociatedProgrammeConstant,
    BreakdownType as BreakdownTypeConstant,
    BusinessPotential as BusinessPotentialConstant,
    Country as CountryConstant,
    ExpectedValueRelation as ExpectedValueRelationConstant,
    ExperienceCategories as ExperienceCategoriesConstant,
    HQTeamRegionOrPost as HQTeamRegionOrPostConstant,
    Sector as SectorConstant,
    SupportType as SupportTypeConstant,
    TeamType as TeamTypeConstant,
    UKRegion as UKRegionConstant,
    WinType as WinTypeConstant,
)
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_date_or_datetime,
)
from datahub.export_win.models import Win
from datahub.export_win.test.factories import (
    BreakdownFactory,
    CustomerResponseFactory,
    WinFactory,
)
from datahub.metadata.test.factories import TeamFactory

pytestmark = pytest.mark.django_db


class TestGetWinView(APITestMixin):
    """Get single win view tests."""

    def test_win_details_no_permissions(self):
        """Should return 403"""
        win = WinFactory()
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:export-win:item', kwargs={'pk': win.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get(self):
        """Test getting a single win."""
        contact = ContactFactory()
        win = WinFactory(
            company_contacts=[contact],
            associated_programme=[
                AssociatedProgrammeConstant.afterburner.value.id,
            ],
            type_of_support=[
                SupportTypeConstant.political_and_economic_briefing.value.id,
            ],
        )
        breakdowns = BreakdownFactory.create_batch(3, win=win)
        customer_response = CustomerResponseFactory(win=win)
        url = reverse('api-v4:export-win:item', kwargs={'pk': win.pk})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        associated_programme = win.associated_programme.first()
        type_of_support = win.type_of_support.first()

        response_breakdowns = sorted(response_data.pop('breakdowns'), key=lambda k: k['id'])

        expected_breakdowns = [{
            'id': str(breakdown.id),
            'type': {
                'id': str(breakdown.type.id),
                'name': breakdown.type.name,
            },
            'value': breakdown.value,
            'year': breakdown.year,
        } for breakdown in breakdowns]
        expected_breakdowns = sorted(expected_breakdowns, key=lambda k: k['id'])

        assert response_breakdowns == expected_breakdowns

        expected_response_data = {
            'id': str(win.id),
            'adviser': {
                'id': str(win.adviser.id),
                'first_name': win.adviser.first_name,
                'last_name': win.adviser.last_name,
                'name': win.adviser.name,
            },
            'company': {
                'id': str(win.company.id),
                'name': win.company.name,
            },
            'country': {
                'id': str(win.country.id),
                'name': win.country.name,
            },
            'associated_programme': [
                {
                    'id': str(associated_programme.id),
                    'name': associated_programme.name,
                },
            ],
            'company_contacts': [
                {
                    'id': str(contact.id),
                    'name': contact.name,
                    'email': contact.email,
                },
            ],
            'audit': win.audit,
            'business_potential': {
                'id': str(win.business_potential.id),
                'name': win.business_potential.name,
            },
            'business_type': win.business_type,
            'complete': win.complete,
            'created_on': format_date_or_datetime(win.created_on),
            'customer_location': {
                'id': str(win.customer_location.id),
                'name': win.customer_location.name,
            },
            'date': format_date_or_datetime(win.date),
            'description': win.description,
            'export_experience': {
                'id': str(win.export_experience.id),
                'name': win.export_experience.name,
            },
            'goods_vs_services': {
                'id': str(win.goods_vs_services.id),
                'name': win.goods_vs_services.name,
            },
            'has_hvo_specialist_involvement': win.has_hvo_specialist_involvement,
            'hq_team': {
                'id': str(win.hq_team.id),
                'name': win.hq_team.name,
            },
            'hvc': {
                'id': str(win.hvc.id),
                'name': win.hvc.name,
            },
            'hvo_programme': None,
            'is_e_exported': win.is_e_exported,
            'is_line_manager_confirmed': win.is_line_manager_confirmed,
            'is_personally_confirmed': win.is_personally_confirmed,
            'is_prosperity_fund_related': win.is_prosperity_fund_related,
            'lead_officer': {
                'id': str(win.lead_officer.id),
                'first_name': win.lead_officer.first_name,
                'last_name': win.lead_officer.last_name,
                'name': win.lead_officer.name,
            },
            'location': win.location,
            'modified_on': format_date_or_datetime(win.modified_on),
            'name_of_customer': win.name_of_customer,
            'name_of_customer_confidential': win.name_of_customer_confidential,
            'name_of_export': win.name_of_export,
            'sector': {
                'id': str(win.sector.id),
                'name': win.sector.name,
            },
            'team_type': {
                'id': str(win.team_type.id),
                'name': win.team_type.name,
            },
            'total_expected_export_value': win.total_expected_export_value,
            'total_expected_non_export_value': win.total_expected_non_export_value,
            'total_expected_odi_value': win.total_expected_odi_value,
            'type': {
                'id': str(win.type.id),
                'name': win.type.name,
            },
            'type_of_support': [
                {
                    'id': str(type_of_support.id),
                    'name': type_of_support.name,
                },
            ],
            'team_members': [],
            'advisers': [],
            'customer_response': {
                'id': str(customer_response.id),
                'access_to_contacts': {
                    'id': str(customer_response.access_to_contacts.id),
                    'name': customer_response.access_to_contacts.name,
                },
                'access_to_information': {
                    'id': str(customer_response.access_to_information.id),
                    'name': customer_response.access_to_information.name,
                },
                'developed_relationships': {
                    'id': str(customer_response.developed_relationships.id),
                    'name': customer_response.developed_relationships.name,
                },
                'expected_portion_without_help': {
                    'id': str(customer_response.expected_portion_without_help.id),
                    'name': customer_response.expected_portion_without_help.name,
                },
                'gained_confidence': {
                    'id': str(customer_response.gained_confidence.id),
                    'name': customer_response.gained_confidence.name,
                },
                'improved_profile': {
                    'id': str(customer_response.improved_profile.id),
                    'name': customer_response.improved_profile.name,
                },
                'last_export': {
                    'id': str(customer_response.last_export.id),
                    'name': customer_response.last_export.name,
                },
                'marketing_source': {
                    'id': str(customer_response.marketing_source.id),
                    'name': customer_response.marketing_source.name,
                },
                'our_support': {
                    'id': str(customer_response.our_support.id),
                    'name': customer_response.our_support.name,
                },
                'overcame_problem': {
                    'id': str(customer_response.overcame_problem.id),
                    'name': customer_response.overcame_problem.name,
                },
                'agree_with_win': customer_response.agree_with_win,
                'case_study_willing': customer_response.case_study_willing,
                'comments': customer_response.comments,
                'company_was_at_risk_of_not_exporting':
                    customer_response.company_was_at_risk_of_not_exporting,
                'has_enabled_expansion_into_existing_market':
                    customer_response.has_enabled_expansion_into_existing_market,
                'has_enabled_expansion_into_new_market':
                    customer_response.has_enabled_expansion_into_new_market,
                'has_explicit_export_plans': customer_response.has_explicit_export_plans,
                'has_increased_exports_as_percent_of_turnover':
                    customer_response.has_increased_exports_as_percent_of_turnover,
                'involved_state_enterprise': customer_response.involved_state_enterprise,
                'name': customer_response.name,
                'other_marketing_source': customer_response.other_marketing_source,
                'support_improved_speed': customer_response.support_improved_speed,
            },
        }

        assert response_data == expected_response_data


class TestListWinView(APITestMixin):
    """List export wins view tests."""

    def test_event_list_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:export-win:collection')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list(self):
        """Tests listing events."""
        WinFactory.create_batch(2)
        url = reverse('api-v4:export-win:collection')

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data['count'] == 2


class TestCreateWinView(APITestMixin):
    """Create export win view tests."""

    def test_create_win_required_only(self):
        """Tests successfully creating an export win with required fields only."""
        url = reverse('api-v4:export-win:collection')

        adviser = AdviserFactory()
        lead_officer = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        date_won = now().date()

        request_data = {
            'adviser': {
                'id': str(adviser.id),
            },
            'lead_officer': {
                'id': str(lead_officer.id),
            },
            'hq_team': {
                'id': HQTeamRegionOrPostConstant.td_events_services.value.id,
            },
            'team_type': {
                'id': TeamTypeConstant.itt.value.id,
            },
            'business_potential': {
                'id': BusinessPotentialConstant.high_export_potential.value.id,
            },
            'company': {
                'id': str(company.id),
            },
            'company_contacts': [
                {
                    'id': str(contact.id),
                },
            ],
            'customer_location': {
                'id': UKRegionConstant.england.value.id,
            },
            'business_type': 'The best type',
            'description': 'Description',
            'name_of_export': 'Sand',
            'date': date_won,
            'country': CountryConstant.canada.value.id,
            'type': {
                'id': WinTypeConstant.both.value.id,
            },
            'total_expected_export_value': 1000000,
            'total_expected_non_export_value': 1000000,
            'total_expected_odi_value': 1000000,
            'goods_vs_services': {
                'id': ExpectedValueRelationConstant.both.value.id,
            },
            'sector': {
                'id': SectorConstant.aerospace_assembly_aircraft.value.id,
            },
            'type_of_support': [
                {
                    'id': SupportTypeConstant.political_and_economic_briefing.value.id,
                },
            ],
            'associated_programme': [
                {
                    'id': AssociatedProgrammeConstant.afterburner.value.id,
                },
            ],
            'is_personally_confirmed': False,
            'is_line_manager_confirmed': False,
            'name_of_customer': 'Overseas Customer',
            'name_of_customer_confidential': True,
            'export_experience': {
                'id': ExperienceCategoriesConstant.never_exported.value.id,
            },
            'breakdowns': [
                {
                    'type': {
                        'id': BreakdownTypeConstant.export.value.id,
                    },
                    'value': 1000,
                    'year': 2023,
                },
            ],
        }
        response = self.api_client.post(url, data=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_201_CREATED
        win = Win.objects.get(id=response_data['id'])
        associated_programme = win.associated_programme.first()
        type_of_support = win.type_of_support.first()

        response_breakdowns = response_data.pop('breakdowns')
        assert len(response_breakdowns) == 1

        expected_breakdown = {
            'id': response_breakdowns[0]['id'],
            'type': {
                'id': BreakdownTypeConstant.export.value.id,
                'name': BreakdownTypeConstant.export.value.name,
            },
            'value': 1000,
            'year': 2023,
        }

        assert response_breakdowns[0] == expected_breakdown

        expected_response_data = {
            'id': str(win.id),
            'adviser': {
                'id': str(win.adviser_id),
                'first_name': win.adviser.first_name,
                'last_name': win.adviser.last_name,
                'name': win.adviser.name,
            },
            'company': {'id': str(win.company_id), 'name': win.company.name},
            'country': {'id': str(win.country_id), 'name': win.country.name},
            'associated_programme': [
                {
                    'id': str(associated_programme.id),
                    'name': associated_programme.name,
                },
            ],
            'company_contacts': [
                {
                    'id': str(contact.id),
                    'name': contact.name,
                    'email': contact.email,
                },
            ],
            'audit': win.audit,
            'business_potential': {
                'id': str(win.business_potential_id),
                'name': win.business_potential.name,
            },
            'business_type': win.business_type,
            'complete': win.complete,
            'created_on': format_date_or_datetime(win.created_on),
            'customer_location': {
                'id': str(win.customer_location_id),
                'name': win.customer_location.name,
            },
            'customer_response': None,
            'date': format_date_or_datetime(win.date),
            'description': win.description,
            'export_experience': {
                'id': str(win.export_experience_id),
                'name': win.export_experience.name,
            },
            'goods_vs_services': {
                'id': str(win.goods_vs_services_id),
                'name': win.goods_vs_services.name,
            },
            'has_hvo_specialist_involvement': win.has_hvo_specialist_involvement,
            'hq_team': {
                'id': str(win.hq_team_id),
                'name': win.hq_team.name,
            },
            'hvc': win.hvc,
            'hvo_programme': None,
            'is_e_exported': win.is_e_exported,
            'is_line_manager_confirmed': win.is_line_manager_confirmed,
            'is_personally_confirmed': win.is_personally_confirmed,
            'is_prosperity_fund_related': win.is_prosperity_fund_related,
            'lead_officer': {
                'id': str(win.lead_officer_id),
                'first_name': win.lead_officer.first_name,
                'last_name': win.lead_officer.last_name,
                'name': win.lead_officer.name,
            },
            'location': win.location,
            'modified_on': format_date_or_datetime(win.modified_on),
            'name_of_customer': win.name_of_customer,
            'name_of_customer_confidential': win.name_of_customer_confidential,
            'name_of_export': win.name_of_export,
            'sector': {'id': str(win.sector_id), 'name': win.sector.name},
            'team_type': {'id': str(win.team_type_id), 'name': win.team_type.name},
            'total_expected_export_value': win.total_expected_export_value,
            'total_expected_non_export_value': win.total_expected_non_export_value,
            'total_expected_odi_value': win.total_expected_odi_value,
            'type': {'id': str(win.type_id), 'name': win.type.name},
            'type_of_support': [{'id': str(type_of_support.id), 'name': type_of_support.name}],
            'team_members': [],
            'advisers': [],
        }

        assert response_data == expected_response_data

    def test_create_win_all_fields(self):
        """Tests successfully creating an export win with all fields only."""
        url = reverse('api-v4:export-win:collection')

        adviser = AdviserFactory()
        additional_team_member = AdviserFactory()
        team_member = AdviserFactory()
        lead_officer = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        date_won = now().date()

        request_data = {
            'adviser': {
                'id': str(adviser.id),
            },
            'lead_officer': {
                'id': str(lead_officer.id),
            },
            'hq_team': {
                'id': HQTeamRegionOrPostConstant.td_events_services.value.id,
            },
            'team_type': {
                'id': TeamTypeConstant.itt.value.id,
            },
            'business_potential': {
                'id': BusinessPotentialConstant.high_export_potential.value.id,
            },
            'company': {
                'id': str(company.id),
            },
            'company_contacts': [
                {
                    'id': str(contact.id),
                },
            ],
            'customer_location': {
                'id': UKRegionConstant.england.value.id,
            },
            'business_type': 'The best type',
            'description': 'Description',
            'name_of_export': 'Sand',
            'date': date_won,
            'country': CountryConstant.canada.value.id,
            'type': {
                'id': WinTypeConstant.both.value.id,
            },
            'total_expected_export_value': 1000000,
            'total_expected_non_export_value': 1000000,
            'total_expected_odi_value': 1000000,
            'goods_vs_services': {
                'id': ExpectedValueRelationConstant.both.value.id,
            },
            'sector': {
                'id': SectorConstant.aerospace_assembly_aircraft.value.id,
            },
            'type_of_support': [
                {
                    'id': SupportTypeConstant.political_and_economic_briefing.value.id,
                },
            ],
            'associated_programme': [
                {
                    'id': AssociatedProgrammeConstant.afterburner.value.id,
                },
            ],
            'is_personally_confirmed': False,
            'is_line_manager_confirmed': False,
            'name_of_customer': 'Overseas Customer',
            'name_of_customer_confidential': True,
            'export_experience': {
                'id': ExperienceCategoriesConstant.never_exported.value.id,
            },
            'breakdowns': [
                {
                    'type': {
                        'id': BreakdownTypeConstant.export.value.id,
                    },
                    'value': 1000,
                    'year': 2023,
                },
            ],
            'team_members': [
                {
                    'id': str(team_member.id),
                },
            ],
            'advisers': [
                {
                    'adviser': {
                        'id': str(additional_team_member.id),
                    },
                    'hq_team': {
                        'id': HQTeamRegionOrPostConstant.td_events_services.value.id,
                    },
                    'team_type': {
                        'id': TeamTypeConstant.itt.value.id,
                    },
                },
            ],
        }
        response = self.api_client.post(url, data=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_201_CREATED
        win = Win.objects.get(id=response_data['id'])
        associated_programme = win.associated_programme.first()
        type_of_support = win.type_of_support.first()

        response_breakdowns = response_data.pop('breakdowns')
        assert len(response_breakdowns) == 1

        expected_breakdown = {
            'id': response_breakdowns[0]['id'],
            'type': {
                'id': BreakdownTypeConstant.export.value.id,
                'name': BreakdownTypeConstant.export.value.name,
            },
            'value': 1000,
            'year': 2023,
        }

        assert response_breakdowns[0] == expected_breakdown

        win_adviser = win.advisers.first()
        expected_team_member = win.team_members.first()

        expected_response_data = {
            'id': str(win.id),
            'adviser': {
                'id': str(win.adviser_id),
                'first_name': win.adviser.first_name,
                'last_name': win.adviser.last_name,
                'name': win.adviser.name,
            },
            'company': {
                'id': str(win.company_id),
                'name': win.company.name,
            },
            'country': {
                'id': str(win.country_id),
                'name': win.country.name,
            },
            'associated_programme': [
                {
                    'id': str(associated_programme.id),
                    'name': associated_programme.name,
                },
            ],
            'company_contacts': [
                {
                    'id': str(contact.id),
                    'name': contact.name,
                    'email': contact.email,
                },
            ],
            'audit': win.audit,
            'business_potential': {
                'id': str(win.business_potential_id),
                'name': win.business_potential.name,
            },
            'business_type': win.business_type,
            'complete': win.complete,
            'created_on': format_date_or_datetime(win.created_on),
            'customer_location': {
                'id': str(win.customer_location_id),
                'name': win.customer_location.name,
            },
            'customer_response': None,
            'date': format_date_or_datetime(win.date),
            'description': win.description,
            'export_experience': {
                'id': str(win.export_experience_id),
                'name': win.export_experience.name,
            },
            'goods_vs_services': {
                'id': str(win.goods_vs_services_id),
                'name': win.goods_vs_services.name,
            },
            'has_hvo_specialist_involvement': win.has_hvo_specialist_involvement,
            'hq_team': {
                'id': str(win.hq_team_id),
                'name': win.hq_team.name,
            },
            'hvc': win.hvc,
            'hvo_programme': None,
            'is_e_exported': win.is_e_exported,
            'is_line_manager_confirmed': win.is_line_manager_confirmed,
            'is_personally_confirmed': win.is_personally_confirmed,
            'is_prosperity_fund_related': win.is_prosperity_fund_related,
            'lead_officer': {
                'id': str(win.lead_officer_id),
                'first_name': win.lead_officer.first_name,
                'last_name': win.lead_officer.last_name,
                'name': win.lead_officer.name,
            },
            'location': win.location,
            'modified_on': format_date_or_datetime(win.modified_on),
            'name_of_customer': win.name_of_customer,
            'name_of_customer_confidential': win.name_of_customer_confidential,
            'name_of_export': win.name_of_export,
            'sector': {'id': str(win.sector_id), 'name': win.sector.name},
            'team_type': {'id': str(win.team_type_id), 'name': win.team_type.name},
            'total_expected_export_value': win.total_expected_export_value,
            'total_expected_non_export_value': win.total_expected_non_export_value,
            'total_expected_odi_value': win.total_expected_odi_value,
            'type': {'id': str(win.type_id), 'name': win.type.name},
            'type_of_support': [
                {
                    'id': str(type_of_support.id),
                    'name': type_of_support.name,
                },
            ],
            'team_members': [
                {
                    'id': str(expected_team_member.id),
                    'first_name': expected_team_member.first_name,
                    'last_name': expected_team_member.last_name,
                    'name': expected_team_member.name,
                },
            ],
            'advisers': [
                {
                    'id': str(win_adviser.id),
                    'adviser': {
                        'id': str(win_adviser.adviser.id),
                        'first_name': win_adviser.adviser.first_name,
                        'last_name': win_adviser.adviser.last_name,
                        'name': win_adviser.adviser.name,
                    },
                    'location': win_adviser.location,
                    'team_type': {
                        'id': str(win_adviser.team_type.id),
                        'name': win_adviser.team_type.name,
                    },
                    'hq_team': {
                        'id': str(win_adviser.hq_team.id),
                        'name': win_adviser.hq_team.name,
                    },
                },
            ],
        }

        assert response_data == expected_response_data
