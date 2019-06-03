from cgi import parse_header
from collections import Counter
from csv import DictReader
from datetime import datetime
from io import StringIO
from operator import attrgetter, itemgetter
from random import choice
from uuid import UUID

import factory
import pytest
from dateutil.parser import parse as dateutil_parse
from django.conf import settings
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_csv_data,
    get_attr_or_none,
    join_attr_values,
    random_obj_for_queryset,
)
from datahub.core.utils import join_truthy_strings
from datahub.interaction.models import (
    CommunicationChannel,
    Interaction,
    InteractionPermission,
    PolicyArea,
    PolicyIssueType,
)
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    CompanyInteractionFactoryWithPolicyFeedback,
    EventServiceDeliveryFactory,
    InteractionDITParticipantFactory,
    InvestmentProjectInteractionFactory,
    ServiceDeliveryFactory,
)
from datahub.investment.project.test.factories import ActiveInvestmentProjectFactory
from datahub.metadata.models import Sector
from datahub.metadata.test.factories import TeamFactory
from datahub.search.interaction.views import SearchInteractionExportAPIView

pytestmark = pytest.mark.django_db


@pytest.fixture
def interactions(setup_es):
    """Sets up data for the tests."""
    data = []
    with freeze_time('2017-01-01 13:00:00'):
        company_1 = CompanyFactory(name='ABC Trading Ltd')
        company_2 = CompanyFactory(name='Little Puddle Ltd')
        data.extend([
            CompanyInteractionFactory(
                subject='Exports meeting',
                date=dateutil_parse('2017-10-30T00:00:00Z'),
                company=company_1,
                contacts=[
                    ContactFactory(company=company_1, first_name='Lee', last_name='Danger'),
                    ContactFactory(company=company_1, first_name='Francis', last_name='Brady'),
                    ContactFactory(company=company_1, first_name='Zanger Za', last_name='Qa'),
                ],
                dit_adviser__first_name='Angela',
                dit_adviser__last_name='Lawson',
            ),
            CompanyInteractionFactory(
                subject='a coffee',
                date=dateutil_parse('2017-04-05T00:00:00Z'),
                company=company_2,
                contacts=[
                    ContactFactory(company=company_1, first_name='Try', last_name='Slanger'),
                ],
                dit_adviser__first_name='Zed',
                dit_adviser__last_name='Zeddy',
            ),
            CompanyInteractionFactory(
                subject='Email about exhibition',
                date=dateutil_parse('2016-09-02T00:00:00Z'),
                company=company_2,
                contacts=[
                    ContactFactory(company=company_1, first_name='Caroline', last_name='Green'),
                ],
                dit_adviser__first_name='Prime',
                dit_adviser__last_name='Zeddy',
            ),
            CompanyInteractionFactory(
                subject='talking about cats',
                date=dateutil_parse('2018-02-01T00:00:00Z'),
                company=company_2,
                contacts=[
                    ContactFactory(company=company_1, first_name='Full', last_name='Bridge'),
                ],
                dit_adviser__first_name='Low',
                dit_adviser__last_name='Tremon',
            ),
            CompanyInteractionFactory(
                subject='Event at HQ',
                date=dateutil_parse('2018-01-01T00:00:00Z'),
                company=company_2,
                contacts=[
                    ContactFactory(company=company_1, first_name='Diane', last_name='Pree'),
                ],
                dit_adviser__first_name='Trevor',
                dit_adviser__last_name='Saleman',
            ),
        ])

    setup_es.indices.refresh()

    yield data


class TestInteractionEntitySearchView(APITestMixin):
    """Tests interaction search views."""

    def test_interaction_search_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:search:interaction')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all(self, interactions):
        """
        Tests that all interactions are returned with an empty POST body.
        """
        url = reverse('api-v3:search:interaction')

        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(interactions)
        expected_ids = Counter(str(interaction.id) for interaction in interactions)
        assert Counter([item['id'] for item in response_data['results']]) == expected_ids

    def test_limit(self, interactions):
        """Tests that results can be limited."""
        url = reverse('api-v3:search:interaction')

        request_data = {
            'limit': 1,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['results']) == 1

    def test_offset(self, interactions):
        """Tests that results can be offset."""
        url = reverse('api-v3:search:interaction')

        request_data = {
            'offset': 1,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['results']) == 4

    def test_default_sort(self, setup_es):
        """Tests default sorting of results by date (descending)."""
        url = reverse('api-v3:search:interaction')

        dates = (
            datetime(2017, 2, 4, 13, 15, 0, tzinfo=utc),
            datetime(2017, 1, 4, 11, 23, 10, tzinfo=utc),
            datetime(2017, 9, 29, 3, 25, 15, tzinfo=utc),
            datetime(2017, 7, 5, 11, 44, 33, tzinfo=utc),
            datetime(2017, 2, 1, 18, 15, 1, tzinfo=utc),
        )
        CompanyInteractionFactory.create_batch(
            len(dates),
            date=factory.Iterator(dates),
        )
        setup_es.indices.refresh()

        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        sorted_dates = sorted(dates, reverse=True)
        expected_dates = [d.isoformat() for d in sorted_dates]
        assert response_data['count'] == len(dates)
        assert [item['date'] for item in response_data['results']] == expected_dates

    def test_sort_by_subject_asc(self, interactions):
        """Tests sorting of results by subject (ascending)."""
        url = reverse('api-v3:search:interaction')

        request_data = {
            'sortby': 'subject:asc',
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(interactions)
        subjects = (interaction.subject for interaction in interactions)
        expected_subjects = list(sorted(subjects, key=lambda s: s.lower()))
        assert [item['subject'] for item in response_data['results']] == expected_subjects

    def test_sort_by_subject_desc(self, interactions):
        """Tests sorting of results by subject (ascending)."""
        url = reverse('api-v3:search:interaction')

        request_data = {
            'sortby': 'subject:desc',
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(interactions)
        subjects = (interaction.subject for interaction in interactions)
        expected_subjects = list(sorted(subjects, key=lambda s: s.lower(), reverse=True))
        assert [item['subject'] for item in response_data['results']] == expected_subjects

    @pytest.mark.parametrize(
        'sortby,error',
        (
            ('date:backwards', '"backwards" is not a valid sort direction.'),
            ('gyratory:asc', '"gyratory" is not a valid choice for the sort field.'),
        ),
    )
    def test_sort_by_invalid_field(self, setup_es, sortby, error):
        """Tests attempting to sort by an invalid field and direction."""
        url = reverse('api-v3:search:interaction')

        request_data = {
            'sortby': sortby,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'sortby': [error],
        }

    @pytest.mark.parametrize(
        'term',
        (
            'exports',
            'meeting',
            'exports meeting',
            'danger',
            'dan',
            'dang',
            'FRANCIS',
            'angela',
            'angel',
            'ngel',
            'ela',
            'za',
            'QA',
        ),
    )
    def test_search_original_query(self, interactions, term):
        """Tests searching across fields for a particular interaction."""
        url = reverse('api-v3:search:interaction')

        request_data = {
            'original_query': term,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        interaction = interactions[0]
        assert response_data['count'] == 1
        results = response_data['results']

        for result in results:
            result['contacts'].sort(key=itemgetter('id'))
            result['dit_participants'].sort(
                key=lambda dit_participant: dit_participant['adviser']['id'],
            )

        assert results == [{
            'id': str(interaction.pk),
            'kind': interaction.kind,
            'date': interaction.date.isoformat(),
            'company': {
                'id': str(interaction.company.pk),
                'name': interaction.company.name,
                'trading_names': interaction.company.trading_names,
            },
            'company_sector': {
                'id': str(interaction.company.sector.pk),
                'name': interaction.company.sector.name,
                'ancestors': [{
                    'id': str(ancestor.pk),
                } for ancestor in interaction.company.sector.get_ancestors()],
            },
            'contacts': [
                {
                    'id': str(contact.pk),
                    'first_name': contact.first_name,
                    'name': contact.name,
                    'last_name': contact.last_name,
                }
                for contact in sorted(interaction.contacts.all(), key=attrgetter('id'))
            ],
            'is_event': None,
            'event': None,
            'service': {
                'id': str(interaction.service.pk),
                'name': interaction.service.name,
            },
            'subject': interaction.subject,
            'dit_adviser': {
                'id': str(interaction.dit_adviser.pk),
                'first_name': interaction.dit_adviser.first_name,
                'name': interaction.dit_adviser.name,
                'last_name': interaction.dit_adviser.last_name,
            },
            'dit_participants': [
                {
                    'adviser': {
                        'id': str(dit_participant.adviser.pk),
                        'first_name': dit_participant.adviser.first_name,
                        'name': dit_participant.adviser.name,
                        'last_name': dit_participant.adviser.last_name,
                    },
                    'team': {
                        'id': str(dit_participant.team.pk),
                        'name': dit_participant.team.name,
                    },
                }
                for dit_participant in interaction.dit_participants.order_by('adviser__pk')
            ],
            'notes': interaction.notes,
            'dit_team': {
                'id': str(interaction.dit_team.pk),
                'name': interaction.dit_team.name,
            },
            'communication_channel': {
                'id': str(interaction.communication_channel.pk),
                'name': interaction.communication_channel.name,
            },
            'investment_project': None,
            'investment_project_sector': None,
            'policy_areas': [],
            'policy_issue_types': [],
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'was_policy_feedback_provided': interaction.was_policy_feedback_provided,
            'created_on': interaction.created_on.isoformat(),
            'modified_on': interaction.modified_on.isoformat(),
        }]

    def test_filter_by_kind(self, setup_es):
        """Tests filtering interaction by kind."""
        CompanyInteractionFactory.create_batch(10)
        service_deliveries = ServiceDeliveryFactory.create_batch(10)

        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'kind': Interaction.KINDS.service_delivery,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] == 10

        results = response_data['results']
        service_delivery_ids = {str(interaction.id) for interaction in service_deliveries}
        assert {result['id'] for result in results} == service_delivery_ids

    def test_filter_by_company_id(self, setup_es):
        """Tests filtering interaction by company id."""
        companies = CompanyFactory.create_batch(10)
        CompanyInteractionFactory.create_batch(
            len(companies),
            company=factory.Iterator(companies),
        )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'company': companies[5].id,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] == 1

        results = response_data['results']
        assert results[0]['company']['id'] == str(companies[5].id)

    @pytest.mark.parametrize(
        'name_term,matched_company_name',
        (
            # name
            ('whiskers', 'whiskers and tabby'),
            ('whi', 'whiskers and tabby'),
            ('his', 'whiskers and tabby'),
            ('ers', 'whiskers and tabby'),
            ('1a', '1a'),

            # trading names
            ('maine coon egyptian mau', 'whiskers and tabby'),
            ('maine', 'whiskers and tabby'),
            ('mau', 'whiskers and tabby'),
            ('ine oon', 'whiskers and tabby'),
            ('ine mau', 'whiskers and tabby'),
            ('3a', '1a'),

            # non-matches
            ('whi lorem', None),
            ('wh', None),
            ('whe', None),
            ('tiger', None),
            ('panda', None),
            ('moine', None),
        ),
    )
    def test_filter_by_company_name(self, setup_es, name_term, matched_company_name):
        """Tests filtering interaction by company name."""
        matching_company1 = CompanyFactory(
            name='whiskers and tabby',
            trading_names=['Maine Coon', 'Egyptian Mau'],
        )
        matching_company2 = CompanyFactory(
            name='1a',
            trading_names=['3a', '4a'],
        )
        non_matching_company = CompanyFactory(
            name='Pluto and pippo',
            trading_names=['eniam nooc', 'naitpyge uam'],
        )
        CompanyInteractionFactory(company=matching_company1)
        CompanyInteractionFactory(company=matching_company2)
        CompanyInteractionFactory(company=non_matching_company)

        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')

        response = self.api_client.post(
            url,
            data={
                'original_query': '',
                'company_name': name_term,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        match = Interaction.objects.filter(company__name=matched_company_name).first()
        if match:
            assert response.data['count'] == 1
            assert len(response.data['results']) == 1
            assert response.data['results'][0]['id'] == str(match.id)
        else:
            assert response.data['count'] == 0
            assert len(response.data['results']) == 0

    @pytest.mark.parametrize(
        'created_on_exists',
        (True, False),
    )
    def test_filter_by_created_on_exists(self, setup_es, created_on_exists):
        """Tests filtering interaction by created_on exists."""
        CompanyInteractionFactory.create_batch(3)
        no_created_on = CompanyInteractionFactory.create_batch(3)
        for interaction in no_created_on:
            interaction.created_on = None
            interaction.save()

        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'created_on_exists': created_on_exists,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        results = response_data['results']
        assert response_data['count'] == 3
        assert all(
            (not result['created_on'] is None) == created_on_exists
            for result in results
        )

    def test_filter_by_dit_adviser_id(self, setup_es):
        """Tests filtering interaction by dit adviser id."""
        advisers = AdviserFactory.create_batch(10)
        CompanyInteractionFactory.create_batch(
            len(advisers),
            dit_adviser=factory.Iterator(advisers),
        )

        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'dit_adviser': advisers[5].id,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] == 1

        results = response_data['results']

        assert results[0]['dit_adviser']['id'] == str(advisers[5].id)
        assert results[0]['dit_adviser']['name'] == advisers[5].name

    def test_filter_by_dit_adviser_name(self, setup_es):
        """Tests filtering interaction by dit adviser name."""
        advisers = AdviserFactory.create_batch(10)
        CompanyInteractionFactory.create_batch(
            len(advisers),
            dit_adviser=factory.Iterator(advisers),
        )

        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'dit_adviser_name': advisers[5].name,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] > 0

        results = response_data['results']
        # multiple records can match our filter, let's make sure at least one is exact match
        assert any(result['dit_adviser']['id'] == str(advisers[5].id) for result in results)
        assert any(result['dit_adviser']['name'] == advisers[5].name for result in results)

    def test_filter_by_dit_team(self, setup_es):
        """Tests filtering interaction by dit team."""
        CompanyInteractionFactory.create_batch(5, dit_team_id=constants.Team.crm.value.id)
        dit_team_id = constants.Team.td_events_healthcare.value.id
        CompanyInteractionFactory.create_batch(5, dit_team_id=dit_team_id)

        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'dit_team': dit_team_id,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] == 5

        results = response_data['results']
        assert {result['dit_team']['id'] for result in results} == {str(dit_team_id)}

    @pytest.mark.parametrize('dit_participant_field', ('adviser', 'team'))
    def test_filter_by_dit_participant(self, setup_es, dit_participant_field):
        """Test filtering interaction by DIT participant adviser and team IDs."""
        interactions = CompanyInteractionFactory.create_batch(10, dit_participants=[])
        for interaction in interactions:
            InteractionDITParticipantFactory.create_batch(2, interaction=interaction)

        setup_es.indices.refresh()

        interaction = choice(interactions)
        dit_participant = interaction.dit_participants.order_by('?').first()

        url = reverse('api-v3:search:interaction')
        request_data = {
            f'dit_participants__{dit_participant_field}':
                getattr(dit_participant, dit_participant_field).id,
        }
        response = self.api_client.post(url, request_data)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == 1

        results = response_data['results']
        assert len(results) == 1
        assert results[0]['id'] == str(interaction.pk)

    def test_filter_by_communication_channel(self, setup_es):
        """Tests filtering interaction by interaction type."""
        communication_channels = list(CommunicationChannel.objects.order_by('?')[:2])
        CompanyInteractionFactory.create_batch(
            5,
            communication_channel=communication_channels[0],
        )
        CompanyInteractionFactory.create_batch(
            5,
            communication_channel=communication_channels[1],
        )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'original_query': '',
            'communication_channel': communication_channels[1].pk,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] == 5

        results = response_data['results']
        result_ids = {result['communication_channel']['id'] for result in results}
        assert result_ids == {str(communication_channels[1].pk)}

    @pytest.mark.parametrize(
        'field,field_model',
        (
            ('policy_areas', PolicyArea),
            ('policy_issue_types', PolicyIssueType),
        ),
    )
    def test_filter_by_policy_fields(self, setup_es, field, field_model):
        """
        Tests filtering interactions by:
        - policy area
        - policy issue type
        """
        values = list(field_model.objects.order_by('?')[:2])
        expected_field_value = values[0]
        other_field_value = values[1]

        factory_values = [
            [expected_field_value, other_field_value],
            [expected_field_value, other_field_value],
            [expected_field_value],
            [expected_field_value],
            [expected_field_value],
        ]

        expected_interactions = CompanyInteractionFactoryWithPolicyFeedback.create_batch(
            5,
            **{field: factory.Iterator(factory_values)},
        )

        # Unrelated interactions
        CompanyInteractionFactoryWithPolicyFeedback.create_batch(
            6,
            **{field: [other_field_value]},
        )
        CompanyInteractionFactory.create_batch(6)

        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'original_query': '',
            field: expected_field_value.pk,
        }
        response = self.api_client.post(url, request_data)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        results = response_data['results']
        expected_ids = {str(interaction.pk) for interaction in expected_interactions}

        assert response_data['count'] == 5
        assert Counter(
            value['id']
            for result in results
            for value in result[field]
        ) == {
            str(expected_field_value.pk): 5,
            # two interactions had both values
            str(other_field_value.pk): 2,
        }
        assert {result['id'] for result in results} == expected_ids

    def test_filter_by_service(self, setup_es):
        """Tests filtering interaction by service."""
        CompanyInteractionFactory.create_batch(
            5,
            service_id=constants.Service.trade_enquiry.value.id,
        )
        service_id = constants.Service.account_management.value.id
        CompanyInteractionFactory.create_batch(
            5,
            service_id=service_id,
        )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'service': service_id,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] == 5

        results = response_data['results']
        result_ids = {result['service']['id'] for result in results}
        assert result_ids == {str(service_id)}

    @pytest.mark.parametrize('was_policy_feedback_provided', (False, True))
    def test_filter_by_was_policy_feedback_provided(self, setup_es, was_policy_feedback_provided):
        """Test filtering interactions by was_policy_feedback_provided."""
        interactions_without_policy_feedback = CompanyInteractionFactory.create_batch(5)
        interactions_with_policy_feedback = (
            CompanyInteractionFactoryWithPolicyFeedback.create_batch(5)
        )

        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'was_policy_feedback_provided': was_policy_feedback_provided,
        }
        response = self.api_client.post(url, data=request_data)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        expected_interactions = (
            interactions_with_policy_feedback if was_policy_feedback_provided
            else interactions_without_policy_feedback
        )
        assert response_data['count'] == len(expected_interactions)

        results = response_data['results']
        result_ids = {result['id'] for result in results}
        assert result_ids == {str(interaction.pk) for interaction in expected_interactions}

    @pytest.mark.parametrize(
        'data,results',
        (
            (
                {
                    'date_after': '2017-12-01',
                },
                {
                    'talking about cats',
                    'Event at HQ',
                },
            ),
            (
                {
                    'date_after': '2017-12-01',
                    'date_before': '2018-01-02',
                },
                {
                    'Event at HQ',
                },
            ),
            (
                {
                    'date_before': '2017-01-01',
                },
                {
                    'Email about exhibition',
                },
            ),
        ),
    )
    def test_filter_by_date(self, interactions, data, results):
        """Tests filtering interaction by date."""
        url = reverse('api-v3:search:interaction')
        response = self.api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        names = {result['subject'] for result in response_data['results']}
        assert names == results

    @pytest.mark.parametrize(
        'sector_level',
        (0, 1, 2),
    )
    def test_sector_descends_filter_for_company_interaction(
            self,
            hierarchical_sectors,
            setup_es,
            sector_level,
    ):
        """Test the sector_descends filter with company interactions."""
        num_sectors = len(hierarchical_sectors)
        sectors_ids = [sector.pk for sector in hierarchical_sectors]

        companies = CompanyFactory.create_batch(
            num_sectors,
            sector_id=factory.Iterator(sectors_ids),
        )
        company_interactions = CompanyInteractionFactory.create_batch(
            3,
            company=factory.Iterator(companies),
        )

        other_companies = CompanyFactory.create_batch(
            3,
            sector=factory.LazyFunction(lambda: random_obj_for_queryset(
                Sector.objects.exclude(pk__in=sectors_ids),
            )),
        )
        CompanyInteractionFactory.create_batch(
            3,
            company=factory.Iterator(other_companies),
        )

        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        body = {
            'sector_descends': hierarchical_sectors[sector_level].pk,
        }
        response = self.api_client.post(url, body)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == num_sectors - sector_level

        actual_ids = {UUID(interaction['id']) for interaction in response_data['results']}
        expected_ids = {interaction.pk for interaction in company_interactions[sector_level:]}
        assert actual_ids == expected_ids

    @pytest.mark.parametrize(
        'sector_level',
        (0, 1, 2),
    )
    def test_sector_descends_filter_for_investment_project_interaction(
            self,
            hierarchical_sectors,
            setup_es,
            sector_level,
    ):
        """Test the sector_descends filter with investment project interactions."""
        num_sectors = len(hierarchical_sectors)
        sectors_ids = [sector.pk for sector in hierarchical_sectors]

        projects = ActiveInvestmentProjectFactory.create_batch(
            num_sectors,
            sector_id=factory.Iterator(sectors_ids),
        )
        investment_project_interactions = InvestmentProjectInteractionFactory.create_batch(
            3,
            investment_project=factory.Iterator(projects),
        )

        other_projects = ActiveInvestmentProjectFactory.create_batch(
            3,
            sector=factory.LazyFunction(lambda: random_obj_for_queryset(
                Sector.objects.exclude(pk__in=sectors_ids),
            )),
        )
        InvestmentProjectInteractionFactory.create_batch(
            3,
            investment_project=factory.Iterator(other_projects),
        )

        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        body = {
            'sector_descends': hierarchical_sectors[sector_level].pk,
        }
        response = self.api_client.post(url, body)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == num_sectors - sector_level

        actual_ids = {UUID(interaction['id']) for interaction in response_data['results']}
        expected_ids = {
            interaction.pk for interaction in investment_project_interactions[sector_level:]
        }
        assert actual_ids == expected_ids


class TestInteractionExportView(APITestMixin):
    """Tests the interaction export view."""

    @pytest.mark.parametrize(
        'permissions',
        (
            (),
            (InteractionPermission.view_all,),
            (InteractionPermission.export,),
        ),
    )
    def test_user_without_permission_cannot_export(self, setup_es, permissions):
        """Test that a user without the correct permissions cannot export data."""
        user = create_test_user(dit_team=TeamFactory(), permission_codenames=permissions)
        api_client = self.create_api_client(user=user)

        url = reverse('api-v3:search:interaction-export')
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'request_sortby,orm_ordering',
        (
            (None, '-date'),
            ('date', 'date'),
            ('company.name', 'company__name'),
        ),
    )
    def test_interaction_export(
        self,
        setup_es,
        request_sortby,
        orm_ordering,
    ):
        """
        Test export of interaction search results with a policy feedback user.

        Checks that all interaction kinds except for policy feedback are included in the export.
        """
        # Faker generates job titles containing commas which complicates comparisons,
        # so all contact job titles are explicitly set
        company = CompanyFactory()
        interaction = CompanyInteractionFactory(
            company=company,
            contacts=[
                ContactFactory(company=company, job_title='Engineer'),
                ContactFactory(company=company, job_title=None),
                ContactFactory(company=company, job_title=''),
            ],
        )
        InteractionDITParticipantFactory.create_batch(2, interaction=interaction)
        InteractionDITParticipantFactory(interaction=interaction, team=None)
        InteractionDITParticipantFactory(
            interaction=interaction,
            adviser=None,
            team=factory.SubFactory(TeamFactory),
        )
        EventServiceDeliveryFactory(
            company=company,
            contacts=[
                ContactFactory(company=company, job_title='Managing director'),
            ],
        )
        InvestmentProjectInteractionFactory(
            company=company,
            contacts=[
                ContactFactory(company=company, job_title='Exports manager'),
            ],
        )
        ServiceDeliveryFactory(
            company=company,
            contacts=[
                ContactFactory(company=company, job_title='Sales director'),
            ],
        )
        CompanyInteractionFactoryWithPolicyFeedback(
            company=company,
            contacts=[
                ContactFactory(company=company, job_title='Business development manager'),
            ],
            policy_areas=PolicyArea.objects.order_by('?')[:2],
            policy_issue_types=PolicyIssueType.objects.order_by('?')[:2],
        )

        setup_es.indices.refresh()

        data = {}
        if request_sortby:
            data['sortby'] = request_sortby

        url = reverse('api-v3:search:interaction-export')

        with freeze_time('2018-01-01 11:12:13'):
            response = self.api_client.post(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert parse_header(response.get('Content-Type')) == ('text/csv', {'charset': 'utf-8'})
        assert parse_header(response.get('Content-Disposition')) == (
            'attachment', {'filename': 'Data Hub - Interactions - 2018-01-01-11-12-13.csv'},
        )

        sorted_interactions = Interaction.objects.all().order_by(
            orm_ordering,
            'pk',
        )
        reader = DictReader(StringIO(response.getvalue().decode('utf-8-sig')))

        assert reader.fieldnames == list(SearchInteractionExportAPIView.field_titles.values())

        expected_row_data = [
            {
                'Date': interaction.date,
                'Type': interaction.get_kind_display(),
                'Service': get_attr_or_none(interaction, 'service.name'),
                'Subject': interaction.subject,
                'Link': f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["interaction"]}'
                        f'/{interaction.pk}',
                'Company': get_attr_or_none(interaction, 'company.name'),
                'Company link':
                    f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["company"]}'
                    f'/{interaction.company.pk}',
                'Company country': get_attr_or_none(
                    interaction,
                    'company.address_country.name',
                ),
                'Company UK region': get_attr_or_none(interaction, 'company.uk_region.name'),
                'Company sector': get_attr_or_none(interaction, 'company.sector.name'),
                'Contacts': _format_expected_contacts(interaction),
                'Advisers': _format_expected_advisers(interaction),
                'Event': get_attr_or_none(interaction, 'event.name'),
                'Communication channel':
                    get_attr_or_none(interaction, 'communication_channel.name'),
                'Service delivery status': get_attr_or_none(
                    interaction,
                    'service_delivery_status.name',
                ),
                'Net company receipt': interaction.net_company_receipt,
                'Policy issue types': join_attr_values(interaction.policy_issue_types.all()),
                'Policy areas': join_attr_values(interaction.policy_areas.all(), separator='; '),
                'Policy feedback notes': interaction.policy_feedback_notes,
            }
            for interaction in sorted_interactions
        ]

        actual_row_data = [_format_actual_csv_row(row) for row in reader]
        assert actual_row_data == format_csv_data(expected_row_data)


class TestInteractionBasicSearch(APITestMixin):
    """Tests searching for interactions via basic (global) search."""

    @pytest.mark.parametrize(
        'term',
        (
            'exports',
            'meeting',
            'exports meeting',
            'danger',
            'dan',
            'dang',
            'FRANCIS',
            'angela',
            'angel',
            'ngel',
            'ela',
            'za',
            'QA',
        ),
    )
    def test_search(self, interactions, term):
        """Tests searching for various search terms."""
        url = reverse('api-v3:search:basic')

        request_data = {
            'term': term,
            'entity': 'interaction',
        }
        response = self.api_client.get(url, request_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        interaction = interactions[0]
        assert response_data['count'] == 1
        results = response_data['results']

        for result in results:
            result['contacts'].sort(key=itemgetter('id'))
            result['dit_participants'].sort(
                key=lambda dit_participant: dit_participant['adviser']['id'],
            )

        assert results == [{
            'id': str(interaction.pk),
            'kind': interaction.kind,
            'date': interaction.date.isoformat(),
            'company': {
                'id': str(interaction.company.pk),
                'name': interaction.company.name,
                'trading_names': interaction.company.trading_names,
            },
            'company_sector': {
                'id': str(interaction.company.sector.pk),
                'name': interaction.company.sector.name,
                'ancestors': [{
                    'id': str(ancestor.pk),
                } for ancestor in interaction.company.sector.get_ancestors()],
            },
            'contacts': [
                {
                    'id': str(contact.pk),
                    'first_name': contact.first_name,
                    'name': contact.name,
                    'last_name': contact.last_name,
                }
                for contact in sorted(interaction.contacts.all(), key=attrgetter('id'))
            ],
            'is_event': None,
            'event': None,
            'service': {
                'id': str(interaction.service.pk),
                'name': interaction.service.name,
            },
            'subject': interaction.subject,
            'dit_adviser': {
                'id': str(interaction.dit_adviser.pk),
                'first_name': interaction.dit_adviser.first_name,
                'name': interaction.dit_adviser.name,
                'last_name': interaction.dit_adviser.last_name,
            },
            'dit_participants': [
                {
                    'adviser': {
                        'id': str(dit_participant.adviser.pk),
                        'first_name': dit_participant.adviser.first_name,
                        'name': dit_participant.adviser.name,
                        'last_name': dit_participant.adviser.last_name,
                    },
                    'team': {
                        'id': str(dit_participant.team.pk),
                        'name': dit_participant.team.name,
                    },
                }
                for dit_participant in interaction.dit_participants.order_by('adviser__pk')
            ],
            'notes': interaction.notes,
            'dit_team': {
                'id': str(interaction.dit_team.pk),
                'name': interaction.dit_team.name,
            },
            'communication_channel': {
                'id': str(interaction.communication_channel.pk),
                'name': interaction.communication_channel.name,
            },
            'investment_project': None,
            'investment_project_sector': None,
            'policy_areas': [],
            'policy_issue_types': [],
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'was_policy_feedback_provided': interaction.was_policy_feedback_provided,
            'created_on': interaction.created_on.isoformat(),
            'modified_on': interaction.modified_on.isoformat(),
        }]


def _format_expected_contacts(interaction):
    formatted_contact_names = sorted(
        [_format_expected_contact_name(contact) for contact in interaction.contacts.all()],
    )
    return ', '.join(formatted_contact_names)


def _format_expected_contact_name(contact):
    if contact.job_title:
        return f'{contact.name} ({contact.job_title})'

    return f'{contact.name}'


def _format_expected_advisers(interaction):
    formatted_contact_names = sorted(
        _format_expected_adviser_name(dit_participant)
        for dit_participant in interaction.dit_participants.all()
    )
    return ', '.join(formatted_contact_names)


def _format_expected_adviser_name(dit_participant):
    adviser_name = dit_participant.adviser.name if dit_participant.adviser else ''
    team_name = f'({dit_participant.team.name})' if dit_participant.team else ''
    return join_truthy_strings(adviser_name, team_name)


def _format_actual_csv_row(row):
    return {key: _format_actual_csv_value(key, value) for key, value in row.items()}


def _format_actual_csv_value(key, value):
    """
    Sorts the value of multi-value fields for a row alphabetically as they are unordered at
    present.

    TODO Django 2.2 added ordering support to StringAgg, which will remove the need for this.
     However, it is not currently used due to https://code.djangoproject.com/ticket/30315.
    """
    multi_value_fields_and_separators = {
        'Advisers': ', ',
        'Contacts': ', ',
        'Policy areas': '; ',
        'Policy issue types': ', ',
    }

    if key in multi_value_fields_and_separators:
        separator = multi_value_fields_and_separators[key]
        sorted_split_values = sorted(value.split(separator))
        return separator.join(sorted_split_values)

    return value
