import datetime
from unittest import mock

import pytest

from django.conf import settings
from django.utils.timezone import now
from freezegun import freeze_time

from rest_framework import status
from rest_framework.reverse import reverse
from reversion.models import Version

from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    ContactFactory,
    ExportExperienceFactory,
    ExportFactory,
)
from datahub.core.constants import (
    AssociatedProgramme as AssociatedProgrammeConstant,
    BreakdownType as BreakdownTypeConstant,
    BusinessPotential as BusinessPotentialConstant,
    Country as CountryConstant,
    ExpectedValueRelation as ExpectedValueRelationConstant,
    HQTeamRegionOrPost as HQTeamRegionOrPostConstant,
    Sector as SectorConstant,
    SupportType as SupportTypeConstant,
    TeamType as TeamTypeConstant,
    WinType as WinTypeConstant,
    WinUKRegion as WinUKRegionConstant,
)
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_date_or_datetime,
)
from datahub.export_win import (
    EXPORT_WINS_LEGACY_DATA_FEATURE_FLAG_NAME,
)
from datahub.export_win.models import (
    CustomerResponse,
    CustomerResponseToken,
    Win,
)
from datahub.export_win.tasks import (
    update_customer_response_token_for_email_notification_id,
)
from datahub.export_win.test.factories import (
    BreakdownFactory,
    CustomerResponseFactory,
    CustomerResponseTokenFactory,
    WinAdviserFactory,
    WinFactory,
)
from datahub.feature_flag.test.factories import UserFeatureFlagFactory
from datahub.metadata.test.factories import TeamFactory

pytestmark = pytest.mark.django_db


@pytest.fixture()
def export_wins_legacy_data_feature_flag():
    """
    Creates the Export wins legacy data user feature flag.
    """
    yield UserFeatureFlagFactory(
        code=EXPORT_WINS_LEGACY_DATA_FEATURE_FLAG_NAME,
        is_active=True,
    )


@pytest.fixture()
def export_wins():
    confirmed = CustomerResponseFactory.create_batch(
        2,
        agree_with_win=True,
        responded_on=datetime.datetime.utcnow(),
    )
    unconfirmed = CustomerResponseFactory.create_batch(
        3,
        agree_with_win=False,
        responded_on=datetime.datetime.utcnow(),
    )
    awaiting = CustomerResponseFactory(agree_with_win=None)
    yield [
        confirmed,
        unconfirmed,
        awaiting,
    ]


def mock_export_win_create_token(monkeypatch):
    mock_create_token = mock.Mock()
    monkeypatch.setattr(
        'datahub.export_win.tasks.create_token_for_contact',
        mock_create_token,
    )
    return mock_create_token


@pytest.fixture()
def mock_export_win_get_all_fields(monkeypatch):
    mock_get_all_fields = mock.Mock()
    monkeypatch.setattr(
        'datahub.export_win.tasks.get_all_fields_for_client_email_receipt',
        mock_get_all_fields,
    )
    return mock_get_all_fields


@pytest.fixture()
def mock_notify_export_win_email_by_rq_email(monkeypatch):
    mock_contact_by_rq_email = mock.Mock()
    monkeypatch.setattr(
        'datahub.export_win.views.notify_export_win_email_by_rq_email',
        mock_contact_by_rq_email,
    )
    return mock_contact_by_rq_email


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
        export = ExportFactory()
        export_experience = ExportExperienceFactory()
        win = WinFactory(
            adviser=self.user,
            company_contacts=[contact],
            associated_programme=[
                AssociatedProgrammeConstant.afterburner.value.id,
            ],
            type_of_support=[
                SupportTypeConstant.political_and_economic_briefing.value.id,
            ],
            export_experience=export_experience,
            company_export=export,
        )
        breakdowns = BreakdownFactory.create_batch(3, win=win)
        customer_response = CustomerResponseFactory(win=win)

        first_sent = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
        with freeze_time(first_sent):
            CustomerResponseTokenFactory(
                customer_response=win.customer_response,
            )
        last_sent = datetime.datetime(year=2012, month=7, day=19, hour=15, minute=6, second=3)
        with freeze_time(last_sent):
            CustomerResponseTokenFactory(
                customer_response=win.customer_response,
            )

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
            # legacy field
            'adviser_name': win.adviser_name,
            # legacy field
            'adviser_email_address': win.adviser_email_address,
            'company': {
                'id': str(win.company.id),
                'name': win.company.name,
            },
            # legacy field
            'company_name': win.company_name,
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
            # legacy field
            'customer_name': win.customer_name,
            # legacy field
            'customer_email_address': win.customer_email_address,
            # legacy field
            'customer_job_title': win.customer_job_title,
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
                'id': str(export_experience.id),
                'name': export_experience.name,
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
            # legacy field
            'lead_officer_name': win.lead_officer_name,
            # legacy field
            'lead_officer_email_address': win.lead_officer_email_address,
            'location': win.location,
            'modified_on': format_date_or_datetime(win.modified_on),
            'migrated_on': format_date_or_datetime(win.migrated_on),
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
                'responded_on': customer_response.responded_on,
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
                'interventions_were_prerequisite':
                    customer_response.interventions_were_prerequisite,
                'name': customer_response.name,
                'other_marketing_source': customer_response.other_marketing_source,
                'support_improved_speed': customer_response.support_improved_speed,
            },
            'company_export': {
                'id': str(export.id),
                'title': export.title,
            },
            'first_sent': format_date_or_datetime(first_sent),
            'last_sent': format_date_or_datetime(last_sent),
        }

        assert response_data == expected_response_data

    @pytest.mark.parametrize(
        'params,related_objects,status_code',
        (
            (
                lambda self: {'adviser': self.user},
                lambda self, win: None,
                status.HTTP_200_OK,
            ),
            (
                lambda self: {'lead_officer': self.user},
                lambda self, win: None,
                status.HTTP_200_OK,
            ),
            (
                lambda self: {'team_members': [self.user]},
                lambda self, win: None,
                status.HTTP_200_OK,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win, adviser=self.user),
                    CustomerResponseFactory(win=win, agree_with_win=True),
                ],
                status.HTTP_200_OK,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win, adviser=self.user),
                    CustomerResponseFactory(win=win, agree_with_win=False),
                ],
                status.HTTP_404_NOT_FOUND,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win, adviser=self.user),
                    CustomerResponseFactory(win=win, agree_with_win=None),
                ],
                status.HTTP_404_NOT_FOUND,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win),
                    CustomerResponseFactory(win=win, agree_with_win=True),
                ],
                status.HTTP_200_OK,
            ),
            (
                lambda self: {},
                lambda self, win: None,
                status.HTTP_404_NOT_FOUND,
            ),
            (
                lambda self: {'is_anonymous_win': True},
                lambda self, win: [
                    WinAdviserFactory(win=win),
                    CustomerResponseFactory(win=win, agree_with_win=True),
                ],
                status.HTTP_404_NOT_FOUND,
            ),
        ),
    )
    def test_get_visibility(self, params, related_objects, status_code):
        """Test getting a single win for different users."""
        resolved_params = params(self)
        win = WinFactory(**resolved_params)
        related_objects(self, win)
        url = reverse('api-v4:export-win:item', kwargs={'pk': win.pk})

        response = self.api_client.get(url)

        assert response.status_code == status_code


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
        """Tests listing wins."""
        WinFactory.create_batch(2, adviser=self.user)
        url = reverse('api-v4:export-win:collection')

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data['count'] == 2

    @pytest.mark.parametrize(
        'list_legacy_data',
        (
            True,
            False,
        ),
    )
    def test_list_with_legacy_wins(self, list_legacy_data, export_wins_legacy_data_feature_flag):
        """Tests listing wins."""
        if list_legacy_data:
            self.user.features.set([export_wins_legacy_data_feature_flag])
        WinFactory.create_batch(2, adviser=self.user)
        WinFactory.create_batch(2, adviser=self.user, migrated_on=now())
        url = reverse('api-v4:export-win:collection')

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data['count'] == (4 if list_legacy_data else 2)

    def test_list_default_sorting(self):
        """Tests wins are sorted."""
        responded_on1 = datetime.datetime(2022, 4, 1)
        responded_on2 = datetime.datetime(2022, 5, 1)
        created_on1 = datetime.datetime(2022, 6, 1)
        created_on2 = datetime.datetime(2022, 7, 1)

        win1 = WinFactory(adviser=self.user)
        CustomerResponseFactory(win=win1, responded_on=responded_on1)
        win2 = WinFactory(adviser=self.user)
        CustomerResponseFactory(win=win2, responded_on=responded_on2)
        with freeze_time(created_on1):
            win3 = WinFactory(adviser=self.user)
            CustomerResponseFactory(win=win3)
        with freeze_time(created_on2):
            win4 = WinFactory(adviser=self.user)
            CustomerResponseFactory(win=win4)

        url = reverse('api-v4:export-win:collection')

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        result_ids = [result['id'] for result in response_data['results']]
        assert result_ids == [str(win4.id), str(win3.id), str(win2.id), str(win1.id)]

    @pytest.mark.parametrize(
        'confirmed,results_length',
        (
            (
                'true',
                2,
            ),
            (
                'false',
                3,
            ),
            (
                'null',
                1,
            ),
        ),
    )
    def test_list_filtered_by_agree_with_win(self, export_wins, confirmed, results_length):
        """Test the HVC view when filtered by financial year"""
        Win.objects.update(adviser=self.user)
        url = reverse('api-v4:export-win:collection')

        response = self.api_client.get(url, data={
            'confirmed': confirmed,
        })
        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        assert len(results['results']) == results_length

        expected = {
            'true': True,
            'false': False,
            'null': None,
        }

        assert all(
            result['customer_response']['agree_with_win'] == expected[confirmed]
            for result in results['results']
        ) is True

    @pytest.mark.parametrize(
        'params,related_objects,results_length',
        (
            (
                lambda self: {'adviser': self.user},
                lambda self, win: None,
                1,
            ),
            (
                lambda self: {'lead_officer': self.user},
                lambda self, win: None,
                1,
            ),
            (
                lambda self: {'team_members': [self.user]},
                lambda self, win: None,
                1,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win, adviser=self.user),
                    CustomerResponseFactory(win=win, agree_with_win=True),
                ],
                1,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win, adviser=self.user),
                    CustomerResponseFactory(win=win, agree_with_win=False),
                ],
                0,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win, adviser=self.user),
                    CustomerResponseFactory(win=win, agree_with_win=None),
                ],
                0,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win),
                    CustomerResponseFactory(win=win, agree_with_win=True),
                ],
                0,
            ),
            (
                lambda self: {},
                lambda self, win: None,
                0,
            ),
            (
                lambda self: {'is_anonymous_win': True},
                lambda self, win: [
                    WinAdviserFactory(win=win, adviser=self.user),
                    CustomerResponseFactory(win=win, agree_with_win=True),
                ],
                0,
            ),
        ),
    )
    def test_list_visibility(self, params, related_objects, results_length):
        """Test getting a list of wins for different users."""
        resolved_params = params(self)
        WinFactory()
        win = WinFactory(**resolved_params)
        related_objects(self, win)
        url = reverse('api-v4:export-win:collection')

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        assert len(results['results']) == results_length
        if results_length == 1:
            assert results['results'][0]['id'] == str(win.id)


class TestCreateWinView(APITestMixin):
    """Create export win view tests."""

    def test_create_win_required_only(self, mock_export_win_serializer_notify):
        """Tests successfully creating an export win with required fields only."""
        url = reverse('api-v4:export-win:collection')

        adviser = self.user
        lead_officer = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        date_won = now().date()
        export_experience = ExportExperienceFactory()

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
                'id': WinUKRegionConstant.overseas.value.id,
            },
            'business_type': 'The best type',
            'description': 'Description',
            'name_of_export': 'Sand',
            'date': date_won,
            'country': CountryConstant.canada.value.id,
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
                'id': str(export_experience.id),
            },
            'breakdowns': [
                {
                    'type': {
                        'id': BreakdownTypeConstant.export.value.id,
                    },
                    'value': 1000,
                    'year': 2,
                },
            ],
        }
        first_sent = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
        with freeze_time(first_sent):
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
            'year': 2,
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
            # legacy field
            'adviser_name': win.adviser_name,
            # legacy field
            'adviser_email_address': win.adviser_email_address,
            'company': {'id': str(win.company_id), 'name': win.company.name},
            # legacy field
            'company_name': win.company_name,
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
            # legacy field
            'customer_name': win.customer_name,
            # legacy field
            'customer_email_address': win.customer_email_address,
            # legacy field
            'customer_job_title': win.customer_job_title,
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
            'customer_response': {
                'access_to_contacts': None,
                'access_to_information': None,
                'agree_with_win': None,
                'responded_on': None,
                'case_study_willing': False,
                'comments': '',
                'company_was_at_risk_of_not_exporting': False,
                'developed_relationships': None,
                'expected_portion_without_help': None,
                'gained_confidence': None,
                'has_enabled_expansion_into_existing_market': False,
                'has_enabled_expansion_into_new_market': False,
                'has_explicit_export_plans': False,
                'has_increased_exports_as_percent_of_turnover': False,
                'id': str(win.customer_response.id),
                'improved_profile': None,
                'involved_state_enterprise': False,
                'interventions_were_prerequisite': False,
                'last_export': None,
                'marketing_source': None,
                'name': '',
                'other_marketing_source': '',
                'our_support': None,
                'overcame_problem': None,
                'support_improved_speed': False,
            },
            'date': format_date_or_datetime(win.date),
            'description': win.description,
            'export_experience': {
                'id': str(export_experience.id),
                'name': export_experience.name,
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
            # legacy field
            'lead_officer_name': win.lead_officer_name,
            # legacy field
            'lead_officer_email_address': win.lead_officer_email_address,
            'location': win.location,
            'modified_on': format_date_or_datetime(win.modified_on),
            'migrated_on': format_date_or_datetime(win.migrated_on),
            'name_of_customer': win.name_of_customer,
            'name_of_customer_confidential': win.name_of_customer_confidential,
            'name_of_export': win.name_of_export,
            'sector': {'id': str(win.sector_id), 'name': win.sector.name},
            'team_type': {'id': str(win.team_type_id), 'name': win.team_type.name},
            'total_expected_export_value': win.total_expected_export_value,
            'total_expected_non_export_value': win.total_expected_non_export_value,
            'total_expected_odi_value': win.total_expected_odi_value,
            'type': None,
            'type_of_support': [{'id': str(type_of_support.id), 'name': type_of_support.name}],
            'team_members': [],
            'advisers': [],
            'first_sent': format_date_or_datetime(first_sent),
            'last_sent': format_date_or_datetime(first_sent),
            'company_export': None,
        }
        # check version created
        assert Version.objects.get_for_object(win).count() == 1
        version = Version.objects.get_for_object(win).first()
        assert version.revision.user == self.user
        assert version.revision.comment == 'Win created'

        assert response_data == expected_response_data
        assert CustomerResponseToken.objects.filter(
            customer_response_id=win.customer_response.id,
            company_contact=win.company_contacts.first(),
        ).exists()
        mock_export_win_serializer_notify.assert_called_once()

    def test_create_win_all_fields(self, mock_export_win_serializer_notify):
        """Tests successfully creating an export win with all fields only."""
        assert Version.objects.count() == 0

        url = reverse('api-v4:export-win:collection')

        adviser = self.user
        additional_team_member = AdviserFactory()
        team_member = AdviserFactory()
        lead_officer = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        date_won = now().date()
        export = ExportFactory()
        export_experience = ExportExperienceFactory()

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
                'id': WinUKRegionConstant.overseas.value.id,
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
                'id': str(export_experience.id),
            },
            'breakdowns': [
                {
                    'type': {
                        'id': BreakdownTypeConstant.export.value.id,
                    },
                    'value': 1000,
                    'year': 5,
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
            'company_export': {
                'id': str(export.id),
            },
        }
        first_sent = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
        with freeze_time(first_sent):
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
            'year': 5,
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
            # legacy field
            'adviser_name': win.adviser_name,
            # legacy field
            'adviser_email_address': win.adviser_email_address,
            'company': {
                'id': str(win.company_id),
                'name': win.company.name,
            },
            # legacy field
            'company_name': win.company_name,
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
            # legacy field
            'customer_name': win.customer_name,
            # legacy field
            'customer_email_address': win.customer_email_address,
            # legacy field
            'customer_job_title': win.customer_job_title,
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
            'customer_response': {
                'access_to_contacts': None,
                'access_to_information': None,
                'agree_with_win': None,
                'responded_on': None,
                'case_study_willing': False,
                'comments': '',
                'company_was_at_risk_of_not_exporting': False,
                'developed_relationships': None,
                'expected_portion_without_help': None,
                'gained_confidence': None,
                'has_enabled_expansion_into_existing_market': False,
                'has_enabled_expansion_into_new_market': False,
                'has_explicit_export_plans': False,
                'has_increased_exports_as_percent_of_turnover': False,
                'id': str(win.customer_response.id),
                'improved_profile': None,
                'involved_state_enterprise': False,
                'interventions_were_prerequisite': False,
                'last_export': None,
                'marketing_source': None,
                'name': '',
                'other_marketing_source': '',
                'our_support': None,
                'overcame_problem': None,
                'support_improved_speed': False,
            },
            'date': format_date_or_datetime(win.date),
            'description': win.description,
            'export_experience': {
                'id': str(export_experience.id),
                'name': export_experience.name,
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
            # legacy field
            'lead_officer_name': win.lead_officer_name,
            # legacy field
            'lead_officer_email_address': win.lead_officer_email_address,
            'location': win.location,
            'modified_on': format_date_or_datetime(win.modified_on),
            'migrated_on': format_date_or_datetime(win.migrated_on),
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
                    # legacy field
                    'name': win_adviser.name,
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
            'company_export': {
                'id': str(export.id),
                'title': export.title,
            },
            'first_sent': format_date_or_datetime(first_sent),
            'last_sent': format_date_or_datetime(first_sent),
        }

        assert response_data == expected_response_data

        # check version created
        assert Version.objects.get_for_object(win).count() == 1
        version = Version.objects.get_for_object(win).first()
        assert version.revision.user == self.user
        assert version.revision.comment == 'Win created'

        assert CustomerResponseToken.objects.filter(
            customer_response_id=win.customer_response.id,
            company_contact=win.company_contacts.first(),
        ).exists()
        mock_export_win_serializer_notify.assert_called_once()

    @pytest.mark.parametrize(
        'request_data',
        (
            'test',
            {'abc': 'def'},
        ),
    )
    def test_create_win_bad_request(self, request_data, caplog):
        """Tests bad requests are being logged."""
        caplog.set_level('ERROR')
        url = reverse('api-v4:export-win:collection')

        response = self.api_client.post(url, data=request_data)
        response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Export Wins API Bad Request' in caplog.text
        assert caplog.records[0].request_data == request_data
        response_text = str(caplog.records[0].response_data)
        assert any([
            'Invalid data' in response_text,
            'This field is required' in response_text,
        ])

    def test_create_win_with_html_script_tags(self, mock_export_win_serializer_notify):
        """Tests handling of HTML/script tags within submitted data."""
        url = reverse('api-v4:export-win:collection')

        # Setup basic data with HTML/script tags in potentially vulnerable fields
        adviser = self.user
        lead_officer = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        date_won = now().date()
        export_experience = ExportExperienceFactory()

        request_data = {
            'adviser': {'id': str(adviser.id)},
            'lead_officer': {'id': str(lead_officer.id)},
            'hq_team': {'id': HQTeamRegionOrPostConstant.td_events_services.value.id},
            'team_type': {'id': TeamTypeConstant.itt.value.id},
            'business_potential': {'id': BusinessPotentialConstant.high_export_potential.value.id},
            'company': {'id': str(company.id)},
            'company_contacts': [{'id': str(contact.id)}],
            'customer_location': {'id': WinUKRegionConstant.overseas.value.id},
            'business_type': 'The best type',
            'description': '<script>alert("XSS");</script>',
            'name_of_export': '<div>Unsafe HTML content</div>',
            'date': date_won,
            'country': CountryConstant.canada.value.id,
            'total_expected_export_value': 1000000,
            'total_expected_non_export_value': 1000000,
            'total_expected_odi_value': 1000000,
            'goods_vs_services': {'id': ExpectedValueRelationConstant.both.value.id},
            'sector': {'id': SectorConstant.aerospace_assembly_aircraft.value.id},
            'type_of_support': [
                {'id': SupportTypeConstant.political_and_economic_briefing.value.id}],
            'associated_programme': [{'id': AssociatedProgrammeConstant.afterburner.value.id}],
            'is_personally_confirmed': False,
            'is_line_manager_confirmed': False,
            'name_of_customer': 'Overseas Customer<script>alert("hack");</script>',
            'name_of_customer_confidential': True,
            'export_experience': {'id': str(export_experience.id)},
            'breakdowns': [{'type': {'id': BreakdownTypeConstant.export.value.id},
                            'value': 1000, 'year': 3}],
        }
        first_sent = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
        with freeze_time(first_sent):
            response = self.api_client.post(url, data=request_data)
        response_data = response.json()

        # Check that the system either cleansed the input or rejected the request
        assert response.status_code == 400
        assert 'error' in response_data
        error_message = response_data['error']

        assert 'Input contains disallowed HTML or script tags or symbols' in error_message, \
            'The error message should warn about script or HTML tags.'

        mock_export_win_serializer_notify.assert_not_called()


class TestUpdateWinView(APITestMixin):
    """Update export win view tests."""

    def test_update_win_all_fields(self):
        """Tests successfully updating an export win with all fields only."""
        win = WinFactory(adviser=self.user)
        customer_response = CustomerResponse(win=win)
        customer_response.save()

        assert Version.objects.count() == 0

        url = reverse('api-v4:export-win:item', kwargs={'pk': win.pk})
        BreakdownFactory.create_batch(3, win=win)
        WinAdviserFactory.create_batch(2, win=win)
        adviser = AdviserFactory()
        additional_team_member = AdviserFactory()
        team_member = AdviserFactory()
        lead_officer = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        date_won = now().date()
        export = ExportFactory()
        export_experience = ExportExperienceFactory()
        first_sent = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
        with freeze_time(first_sent):
            CustomerResponseTokenFactory(
                customer_response=win.customer_response,
            )

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
                'id': WinUKRegionConstant.overseas.value.id,
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
                'id': str(export_experience.id),
            },
            'location': 'Park',
            'breakdowns': [
                {
                    'type': {
                        'id': BreakdownTypeConstant.export.value.id,
                    },
                    'value': 1000,
                    'year': 3,
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
            'company_export': {
                'id': str(export.id),
            },
            # to confirm, the field should not be updated
            'customer_response': None,
        }
        assert win.breakdowns.count() == 3
        assert win.advisers.count() == 2
        assert win.company_export is None
        response = self.api_client.patch(url, data=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        win.refresh_from_db()
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
            'year': 3,
        }

        assert response_breakdowns[0] == expected_breakdown

        win_adviser = win.advisers.first()
        expected_team_member = win.team_members.first()

        expected_response_data = {
            'id': str(win.id),
            'adviser': {
                'id': str(adviser.id),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
            },
            # legacy field
            'adviser_name': win.adviser_name,
            # legacy field
            'adviser_email_address': win.adviser_email_address,
            'company': {
                'id': str(company.id),
                'name': company.name,
            },
            # legacy field
            'company_name': win.company_name,
            'country': {
                'id': str(CountryConstant.canada.value.id),
                'name': CountryConstant.canada.value.name,
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
            # legacy field
            'customer_name': win.customer_name,
            # legacy field
            'customer_email_address': win.customer_email_address,
            # legacy field
            'customer_job_title': win.customer_job_title,
            'audit': win.audit,
            'business_potential': {
                'id': str(win.business_potential_id),
                'name': win.business_potential.name,
            },
            'business_type': 'The best type',
            'complete': win.complete,
            'created_on': format_date_or_datetime(win.created_on),
            'customer_location': {
                'id': WinUKRegionConstant.overseas.value.id,
                'name': WinUKRegionConstant.overseas.value.name,
            },
            'customer_response': {
                'access_to_contacts': None,
                'access_to_information': None,
                'agree_with_win': None,
                'responded_on': None,
                'case_study_willing': False,
                'comments': '',
                'company_was_at_risk_of_not_exporting': False,
                'developed_relationships': None,
                'expected_portion_without_help': None,
                'gained_confidence': None,
                'has_enabled_expansion_into_existing_market': False,
                'has_enabled_expansion_into_new_market': False,
                'has_explicit_export_plans': False,
                'has_increased_exports_as_percent_of_turnover': False,
                'id': str(win.customer_response.id),
                'improved_profile': None,
                'involved_state_enterprise': False,
                'interventions_were_prerequisite': False,
                'last_export': None,
                'marketing_source': None,
                'name': '',
                'other_marketing_source': '',
                'our_support': None,
                'overcame_problem': None,
                'support_improved_speed': False,
            },
            'date': format_date_or_datetime(date_won),
            'description': 'Description',
            'export_experience': {
                'id': str(export_experience.id),
                'name': export_experience.name,
            },
            'goods_vs_services': {
                'id': ExpectedValueRelationConstant.both.value.id,
                'name': ExpectedValueRelationConstant.both.value.name,
            },
            'has_hvo_specialist_involvement': win.has_hvo_specialist_involvement,
            'hq_team': {
                'id': HQTeamRegionOrPostConstant.td_events_services.value.id,
                'name': HQTeamRegionOrPostConstant.td_events_services.value.name,
            },
            'hvc': {
                'id': str(win.hvc.id),
                'name': win.hvc.name,
            },
            'hvo_programme': None,
            'is_e_exported': win.is_e_exported,
            'is_line_manager_confirmed': False,
            'is_personally_confirmed': False,
            'is_prosperity_fund_related': win.is_prosperity_fund_related,
            'lead_officer': {
                'id': str(lead_officer.id),
                'first_name': lead_officer.first_name,
                'last_name': lead_officer.last_name,
                'name': lead_officer.name,
            },
            # legacy field
            'lead_officer_name': win.lead_officer_name,
            # legacy field
            'lead_officer_email_address': win.lead_officer_email_address,
            'location': 'Park',
            'modified_on': format_date_or_datetime(win.modified_on),
            'migrated_on': format_date_or_datetime(win.migrated_on),
            'name_of_customer': win.name_of_customer,
            'name_of_customer_confidential': win.name_of_customer_confidential,
            'name_of_export': win.name_of_export,
            'sector': {'id': str(win.sector_id), 'name': win.sector.name},
            'team_type': {'id': str(win.team_type_id), 'name': win.team_type.name},
            'total_expected_export_value': win.total_expected_export_value,
            'total_expected_non_export_value': win.total_expected_non_export_value,
            'total_expected_odi_value': win.total_expected_odi_value,
            'type': {'id': WinTypeConstant.both.value.id, 'name': WinTypeConstant.both.value.name},
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
                    # legacy field
                    'name': win_adviser.name,
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
            'company_export': {
                'id': str(export.id),
                'title': export.title,
            },
            'first_sent': format_date_or_datetime(first_sent),
            'last_sent': format_date_or_datetime(first_sent),
        }

        assert response_data == expected_response_data

        # check version created
        assert Version.objects.get_for_object(win).count() == 1
        version = Version.objects.get_for_object(win).first()
        assert version.revision.user == self.user
        assert version.revision.comment == 'Win updated'

    def test_doesnt_update_related_fields_when_not_supplied(self):
        """Tests related fields don't get updated when not supplied."""
        company = CompanyFactory()
        contact = ContactFactory(company=company)

        win = WinFactory(
            adviser=self.user,
            company=company,
            company_contacts=[contact],
            type_of_support=[
                SupportTypeConstant.political_and_economic_briefing.value.id,
            ],
            associated_programme=[
                AssociatedProgrammeConstant.afterburner.value.id,
            ],
        )
        customer_response = CustomerResponse(win=win)
        customer_response.save()
        breakdown = BreakdownFactory(win=win)
        win_adviser = WinAdviserFactory(win=win)
        first_sent = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
        with freeze_time(first_sent):
            CustomerResponseTokenFactory(
                customer_response=win.customer_response,
            )

        assert Version.objects.count() == 0

        url = reverse('api-v4:export-win:item', kwargs={'pk': win.pk})
        request_data = {
            'business_type': 'The best type',
            'description': 'Description',
        }
        assert win.breakdowns.count() == 1
        assert win.advisers.count() == 1
        response = self.api_client.patch(url, data=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        win.refresh_from_db()

        response_breakdowns = response_data.pop('breakdowns')
        assert len(response_breakdowns) == 1

        expected_breakdown = {
            'id': str(breakdown.id),
            'type': {
                'id': str(breakdown.type.id),
                'name': breakdown.type.name,
            },
            'value': breakdown.value,
            'year': breakdown.year,
        }

        assert response_breakdowns[0] == expected_breakdown

        expected_response_data = {
            'id': str(win.id),
            'adviser': {
                'id': str(win.adviser.id),
                'first_name': win.adviser.first_name,
                'last_name': win.adviser.last_name,
                'name': win.adviser.name,
            },
            # legacy field
            'adviser_name': win.adviser_name,
            # legacy field
            'adviser_email_address': win.adviser_email_address,
            'company': {
                'id': str(win.company.id),
                'name': win.company.name,
            },
            # legacy field
            'company_name': win.company_name,
            'country': {
                'id': str(win.country.id),
                'name': win.country.name,
            },
            'associated_programme': [
                {
                    'id': AssociatedProgrammeConstant.afterburner.value.id,
                    'name': AssociatedProgrammeConstant.afterburner.value.name,
                },
            ],
            'company_contacts': [
                {
                    'id': str(contact.id),
                    'name': contact.name,
                    'email': contact.email,
                },
            ],
            # legacy field
            'customer_name': win.customer_name,
            # legacy field
            'customer_email_address': win.customer_email_address,
            # legacy field
            'customer_job_title': win.customer_job_title,
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
            # legacy field
            'lead_officer_name': win.lead_officer_name,
            # legacy field
            'lead_officer_email_address': win.lead_officer_email_address,
            'location': win.location,
            'modified_on': format_date_or_datetime(win.modified_on),
            'migrated_on': format_date_or_datetime(win.migrated_on),
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
                    'id': SupportTypeConstant.political_and_economic_briefing.value.id,
                    'name': SupportTypeConstant.political_and_economic_briefing.value.name,
                },
            ],
            'team_members': [],
            'advisers': [
                {
                    'id': str(win_adviser.id),
                    'adviser': {
                        'id': str(win_adviser.adviser.id),
                        'first_name': win_adviser.adviser.first_name,
                        'last_name': win_adviser.adviser.last_name,
                        'name': win_adviser.adviser.name,
                    },
                    # legacy field
                    'name': win_adviser.name,
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
            'customer_response': {
                'access_to_contacts': None,
                'access_to_information': None,
                'agree_with_win': None,
                'responded_on': None,
                'case_study_willing': False,
                'comments': '',
                'company_was_at_risk_of_not_exporting': False,
                'developed_relationships': None,
                'expected_portion_without_help': None,
                'gained_confidence': None,
                'has_enabled_expansion_into_existing_market': False,
                'has_enabled_expansion_into_new_market': False,
                'has_explicit_export_plans': False,
                'has_increased_exports_as_percent_of_turnover': False,
                'id': str(win.customer_response.id),
                'improved_profile': None,
                'involved_state_enterprise': False,
                'interventions_were_prerequisite': False,
                'last_export': None,
                'marketing_source': None,
                'name': '',
                'other_marketing_source': '',
                'our_support': None,
                'overcame_problem': None,
                'support_improved_speed': False,
            },
            'company_export': None,
            'first_sent': format_date_or_datetime(first_sent),
            'last_sent': format_date_or_datetime(first_sent),
        }

        assert response_data == expected_response_data

        # check version created
        assert Version.objects.get_for_object(win).count() == 1
        version = Version.objects.get_for_object(win).first()
        assert version.revision.user == self.user
        assert version.revision.comment == 'Win updated'

    @pytest.mark.parametrize(
        'params,related_objects,status_code',
        (
            (
                lambda self: {'adviser': self.user},
                lambda self, win: None,
                status.HTTP_200_OK,
            ),
            (
                lambda self: {'lead_officer': self.user},
                lambda self, win: None,
                status.HTTP_200_OK,
            ),
            (
                lambda self: {'team_members': [self.user]},
                lambda self, win: None,
                status.HTTP_200_OK,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win, adviser=self.user),
                    CustomerResponseFactory(win=win, agree_with_win=True),
                ],
                status.HTTP_200_OK,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win, adviser=self.user),
                    CustomerResponseFactory(win=win, agree_with_win=False),
                ],
                status.HTTP_404_NOT_FOUND,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win, adviser=self.user),
                    CustomerResponseFactory(win=win, agree_with_win=None),
                ],
                status.HTTP_404_NOT_FOUND,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win),
                    CustomerResponseFactory(win=win, agree_with_win=True),
                ],
                status.HTTP_404_NOT_FOUND,
            ),
            (
                lambda self: {},
                lambda self, win: None,
                status.HTTP_404_NOT_FOUND,
            ),
            (
                lambda self: {'is_anonymous_win': True},
                lambda self, win: [
                    WinAdviserFactory(win=win),
                    CustomerResponseFactory(win=win, agree_with_win=True),
                ],
                status.HTTP_404_NOT_FOUND,
            ),
        ),
    )
    def test_only_users_involved_in_the_win_can_update(self, params, related_objects, status_code):
        """Test only users involved in the win can update."""
        resolved_params = params(self)
        win = WinFactory(description='Not changed', **resolved_params)
        related_objects(self, win)
        assert win.description == 'Not changed'
        url = reverse('api-v4:export-win:item', kwargs={'pk': win.pk})
        request_data = {
            'description': 'Changed',
        }
        response = self.api_client.patch(url, data=request_data)
        assert response.status_code == status_code
        win.refresh_from_db()
        if status_code == status.HTTP_200_OK:
            assert win.description == 'Changed'
        else:
            assert win.description == 'Not changed'

    @pytest.mark.parametrize(
        'request_data',
        (
            'test',
            {'adviser': 'def'},
        ),
    )
    def test_update_win_bad_request(self, request_data, caplog):
        """Tests bad requests are being logged."""
        caplog.set_level('ERROR')
        win = WinFactory(
            adviser=self.user,
        )
        url = reverse('api-v4:export-win:item', kwargs={'pk': win.pk})
        response = self.api_client.patch(url, data=request_data)
        response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Export Wins API Bad Request' in caplog.text
        assert caplog.records[0].request_data == request_data
        response_text = str(caplog.records[0].response_data)
        assert any([
            'Invalid data' in response_text,
            'Must be a valid UUID' in response_text,
        ])

    def test_update_win_with_html_and_script_tags(self):
        """Tests updating an export win with HTML and script tags"""
        win = WinFactory(adviser=self.user)
        customer_response = CustomerResponse(win=win)
        customer_response.save()

        assert Version.objects.count() == 0

        url = reverse('api-v4:export-win:item', kwargs={'pk': win.pk})
        BreakdownFactory.create_batch(3, win=win)
        WinAdviserFactory.create_batch(2, win=win)
        adviser = AdviserFactory()
        additional_team_member = AdviserFactory()
        team_member = AdviserFactory()
        lead_officer = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        date_won = now().date()
        export = ExportFactory()
        export_experience = ExportExperienceFactory()

        malicious_script = '<script>alert("XSS");</script>'
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
                'id': WinUKRegionConstant.overseas.value.id,
            },
            'business_type': malicious_script,  # Injecting script into text field
            'description': malicious_script,  # Another field injection
            'name_of_export': malicious_script,
            'date': date_won,
            'country': CountryConstant.canada.value.id,
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
            'name_of_customer': malicious_script,  # Customer name script injection
            'name_of_customer_confidential': True,
            'export_experience': {
                'id': str(export_experience.id),
            },
            'location': 'Park',
            'breakdowns': [
                {
                    'type': {
                        'id': BreakdownTypeConstant.export.value.id,
                    },
                    'value': 1000,
                    'year': 3,
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
            'company_export': {
                'id': str(export.id),
            },
        }
        response = self.api_client.patch(url, data=request_data)
        response_data = response.json()

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response_data
        assert 'Input contains disallowed HTML or script tags or symbols' in response_data['error']


class TestResendExportWinView(APITestMixin):
    """Tests for the resend_export_win view."""

    def test_resend_export_win_no_permissions(self, api_client):
        """Test attempting to resend without the required permissions."""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        win = WinFactory()
        url = reverse('api-v4:export-win:win-resend', kwargs={'pk': win.pk})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'You do not have permission to perform this action.' in response.data['detail']

    @pytest.mark.parametrize(
        'params,related_objects,resent',
        (
            (
                lambda self: {'adviser': self.user},
                lambda self, win: [
                    CustomerResponseFactory(win=win, agree_with_win=None),
                ],
                True,
            ),
            (
                lambda self: {'lead_officer': self.user},
                lambda self, win: [
                    CustomerResponseFactory(win=win, agree_with_win=None),
                ],
                True,
            ),
            (
                lambda self: {'team_members': [self.user]},
                lambda self, win: [
                    CustomerResponseFactory(win=win, agree_with_win=None),
                ],
                True,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win, adviser=self.user),
                    CustomerResponseFactory(win=win, agree_with_win=True),
                ],
                False,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win, adviser=self.user),
                    CustomerResponseFactory(win=win, agree_with_win=False),
                ],
                False,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win, adviser=self.user),
                    CustomerResponseFactory(win=win, agree_with_win=None),
                ],
                False,
            ),
            (
                lambda self: {},
                lambda self, win: [
                    WinAdviserFactory(win=win),
                    CustomerResponseFactory(win=win, agree_with_win=True),
                ],
                False,
            ),
            (
                lambda self: {},
                lambda self, win: None,
                False,
            ),
        ),
    )
    def test_resend_export_win_success(
            self,
            mock_notify_export_win_email_by_rq_email,
            params,
            related_objects,
            resent,
    ):
        """Test to resend win to the right contact"""
        contact = ContactFactory()
        resolved_params = params(self)
        win = WinFactory(**resolved_params, company_contacts=[contact])
        related_objects(self, win)

        url = reverse('api-v4:export-win:win-resend', kwargs={'pk': win.pk})
        response = self.api_client.post(url)

        if resent:
            assert response.status_code == status.HTTP_200_OK
            assert response.data == {'message': 'Email has successfully been re-sent'}
            token = CustomerResponseToken.objects.first()
            assert token.company_contact == contact
            mock_notify_export_win_email_by_rq_email.assert_called_once_with(
                contact.email,
                settings.EXPORT_WIN_CLIENT_RECEIPT_TEMPLATE_ID,
                {
                    'client_firstname': contact.first_name,
                    'country_destination': str(win.country.name),
                    'customer_email': contact.email,
                    'goods_services': win.goods_vs_services.name,
                    'lead_officer_name': win.lead_officer.name,
                    'url': f'{settings.EXPORT_WIN_CLIENT_REVIEW_WIN_URL}/{token.id}',
                },
                update_customer_response_token_for_email_notification_id,
                token.id,
            )
        else:
            assert response.status_code == status.HTTP_404_NOT_FOUND
            mock_notify_export_win_email_by_rq_email.assert_not_called()
