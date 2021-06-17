from datetime import date
from functools import partial
from itertools import chain
from operator import itemgetter

import pytest
from django.core.exceptions import NON_FIELD_ERRORS, ObjectDoesNotExist
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

from datahub.company.models import (
    Company,
    CompanyExportCountry,
    CompanyExportCountryHistory,
)
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyExportCountryFactory,
    CompanyFactory,
    ContactFactory,
)
from datahub.company.test.utils import format_expected_adviser
from datahub.core.constants import Country, Service
from datahub.core.test_utils import APITestMixin, create_test_user, random_obj_for_model
from datahub.event.test.factories import EventFactory
from datahub.interaction.models import (
    CommunicationChannel,
    Interaction,
    InteractionPermission,
    PolicyArea,
    PolicyIssueType,
    ServiceDeliveryStatus,
)
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    CompanyInteractionFactoryWithPolicyFeedback,
    CompanyReferralInteractionFactory,
    ExportCountriesInteractionFactory,
    InvestmentProjectInteractionFactory,
    LargeCapitalOpportunityInteractionFactory,
)
from datahub.interaction.test.permissions import (
    NON_RESTRICTED_ADD_PERMISSIONS,
    NON_RESTRICTED_CHANGE_PERMISSIONS,
    NON_RESTRICTED_VIEW_PERMISSIONS,
)
from datahub.interaction.test.views.constants import TradeAgreement
from datahub.interaction.test.views.utils import resolve_data
from datahub.investment.opportunity.test.factories import LargeCapitalOpportunityFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata import models as meta_models
from datahub.metadata.test.factories import TeamFactory


class TestAddInteraction(APITestMixin):
    """Tests for the add interaction view."""

    @freeze_time('2017-04-18 13:25:30.986208')
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    @pytest.mark.parametrize(
        'extra_data',
        (
            # company interaction
            {},
            # company interaction with investment theme
            {
                'theme': Interaction.Theme.INVESTMENT,
            },
            # company interaction with blank notes
            {
                'notes': '',
            },
            # company interaction with notes
            {
                'notes': 'hello',
            },
            # interaction with a status
            {
                'status': Interaction.Status.DRAFT,
            },
            # investment project interaction
            {
                'investment_project': InvestmentProjectFactory,
                'notes': 'hello',
            },
            {
                'theme': Interaction.Theme.LARGE_CAPITAL_OPPORTUNITY,
                'large_capital_opportunity': LargeCapitalOpportunityFactory,
            },
            # company interaction with policy feedback
            {
                'was_policy_feedback_provided': True,
                'policy_areas': [
                    partial(random_obj_for_model, PolicyArea),
                ],
                'policy_feedback_notes': 'Policy feedback notes',
                'policy_issue_types': [partial(random_obj_for_model, PolicyIssueType)],
            },
        ),
    )
    def test_add(self, extra_data, permissions):
        """Test add a new interaction."""
        adviser = create_test_user(
            permission_codenames=permissions,
            dit_team=TeamFactory(),
        )
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v4:interaction:collection')
        request_data = {
            'kind': Interaction.Kind.INTERACTION,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_participants': [
                {'adviser': adviser.pk},
            ],
            'company': company.pk,
            'contacts': [contact.pk],
            'service': Service.inbound_referral.value.id,
            'was_policy_feedback_provided': False,
            'has_related_trade_agreements': False,
            'related_trade_agreements': [],
            **resolve_data(extra_data),
        }

        api_client = self.create_api_client(user=adviser)
        response = api_client.post(url, request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'kind': Interaction.Kind.INTERACTION,
            'status': request_data.get('status', Interaction.Status.COMPLETE),
            'theme': request_data.get('theme', None),
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_areas': request_data.get('policy_areas', []),
            'policy_feedback_notes': request_data.get('policy_feedback_notes', ''),
            'policy_issue_types': request_data.get('policy_issue_types', []),
            'was_policy_feedback_provided': request_data.get(
                'was_policy_feedback_provided', False,
            ),
            'communication_channel': {
                'id': str(communication_channel.pk),
                'name': communication_channel.name,
            },
            'subject': 'whatever',
            'date': '2017-04-18',
            'dit_participants': [
                {
                    'adviser': {
                        'id': str(adviser.pk),
                        'first_name': adviser.first_name,
                        'last_name': adviser.last_name,
                        'name': adviser.name,
                    },
                    'team': {
                        'id': str(adviser.dit_team.pk),
                        'name': adviser.dit_team.name,
                    },
                },
            ],
            'notes': request_data.get('notes', ''),
            'company': {
                'id': str(company.pk),
                'name': company.name,
            },
            'companies': [{
                'id': str(company.pk),
                'name': company.name,
            }],
            'contacts': [
                {
                    'id': str(contact.pk),
                    'name': contact.name,
                    'first_name': contact.first_name,
                    'last_name': contact.last_name,
                    'job_title': contact.job_title,
                },
            ],
            'event': None,
            'service': {
                'id': str(Service.inbound_referral.value.id),
                'name': Service.inbound_referral.value.name,
            },
            'service_answers': None,
            'investment_project': request_data.get('investment_project'),
            'archived_documents_url_path': '',
            'were_countries_discussed': None,
            'export_countries': [],
            'created_by': {
                'id': str(adviser.pk),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
            },
            'modified_by': {
                'id': str(adviser.pk),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'company_referral': None,
            'large_capital_opportunity': request_data.get('large_capital_opportunity'),
            'has_related_trade_agreements': request_data.get(
                'has_related_trade_agreements', False,
            ),
            'related_trade_agreements': request_data.get(
                'related_trade_agreements', [],
            ),
        }

    @freeze_time('2017-04-18 13:25:30.986208')
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    @pytest.mark.parametrize(
        'extra_data',
        (
            # company interaction
            {},
            # company interaction with investment theme
            {
                'theme': Interaction.Theme.INVESTMENT,
            },
            # company interaction with blank notes
            {
                'notes': '',
            },
            # company interaction with notes
            {
                'notes': 'hello',
            },
            # interaction with a status
            {
                'status': Interaction.Status.DRAFT,
            },
            # investment project interaction
            {
                'investment_project': InvestmentProjectFactory,
                'notes': 'hello',
            },
            {
                'theme': Interaction.Theme.LARGE_CAPITAL_OPPORTUNITY,
                'large_capital_opportunity': LargeCapitalOpportunityFactory,
            },
            # company interaction with policy feedback
            {
                'was_policy_feedback_provided': True,
                'policy_areas': [
                    partial(random_obj_for_model, PolicyArea),
                ],
                'policy_feedback_notes': 'Policy feedback notes',
                'policy_issue_types': [partial(random_obj_for_model, PolicyIssueType)],
            },
        ),
    )
    def test_add_with_companies(self, extra_data, permissions):
        """Test add a new interaction with companies."""
        adviser = create_test_user(
            permission_codenames=permissions,
            dit_team=TeamFactory(),
        )
        companies = CompanyFactory.create_batch(2)
        contact = ContactFactory(company=companies[0])
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v4:interaction:collection')
        request_data = {
            'kind': Interaction.Kind.INTERACTION,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_participants': [
                {'adviser': adviser.pk},
            ],
            'companies': [company.pk for company in companies],
            'contacts': [contact.pk],
            'service': Service.inbound_referral.value.id,
            'was_policy_feedback_provided': False,
            'has_related_trade_agreements': False,
            'related_trade_agreements': [],
            **resolve_data(extra_data),
        }

        api_client = self.create_api_client(user=adviser)
        response = api_client.post(url, request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        result_companies = set(company['id'] for company in response_data['companies'])

        assert result_companies == set(str(company.id) for company in companies)
        assert response_data['company']['id'] == str(companies[0].pk)

    @freeze_time('2017-04-18 13:25:30.986208')
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    @pytest.mark.parametrize(
        'extra_data',
        (
            # company interaction with export theme
            {
                'theme': Interaction.Theme.EXPORT,
                'were_countries_discussed': False,
            },
            # export countries in an interaction (export and other)
            {
                'theme': Interaction.Theme.EXPORT,
                'were_countries_discussed': True,
                'export_countries': [
                    {
                        'country': {
                            'id': Country.canada.value.id,
                            'name': Country.canada.value.name,
                        },
                        'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                    },
                ],
            },
            {
                'theme': Interaction.Theme.OTHER,
                'were_countries_discussed': True,
                'export_countries': [
                    {
                        'country': {
                            'id': Country.canada.value.id,
                            'name': Country.canada.value.name,
                        },
                        'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                    },
                ],
            },
            # normal interaction with no mention of export countries is valid
            {
                'were_countries_discussed': False,
                'export_countries': [],
            },
        ),
    )
    def test_add_with_export_countries_feature_flag_active(
        self, extra_data, permissions,
    ):
        """
        Test add a new interaction with export countries
        when feature flag is active.
        """
        adviser = create_test_user(
            permission_codenames=permissions,
            dit_team=TeamFactory(),
        )
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v4:interaction:collection')
        request_data = {
            'kind': Interaction.Kind.INTERACTION,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_participants': [
                {'adviser': adviser.pk},
            ],
            'company': company.pk,
            'contacts': [contact.pk],
            'service': Service.inbound_referral.value.id,
            'was_policy_feedback_provided': False,
            'has_related_trade_agreements': False,
            'related_trade_agreements': [],
            **resolve_data(extra_data),
        }
        api_client = self.create_api_client(user=adviser)
        response = api_client.post(url, request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'kind': Interaction.Kind.INTERACTION,
            'status': request_data.get('status', Interaction.Status.COMPLETE),
            'theme': request_data.get('theme', None),
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_areas': request_data.get('policy_areas', []),
            'policy_feedback_notes': request_data.get('policy_feedback_notes', ''),
            'policy_issue_types': request_data.get('policy_issue_types', []),
            'was_policy_feedback_provided': request_data.get(
                'was_policy_feedback_provided', False,
            ),
            'communication_channel': {
                'id': str(communication_channel.pk),
                'name': communication_channel.name,
            },
            'subject': 'whatever',
            'date': '2017-04-18',
            'dit_participants': [
                {
                    'adviser': {
                        'id': str(adviser.pk),
                        'first_name': adviser.first_name,
                        'last_name': adviser.last_name,
                        'name': adviser.name,
                    },
                    'team': {
                        'id': str(adviser.dit_team.pk),
                        'name': adviser.dit_team.name,
                    },
                },
            ],
            'notes': request_data.get('notes', ''),
            'company': {
                'id': str(company.pk),
                'name': company.name,
            },
            'companies': [{
                'id': str(company.pk),
                'name': company.name,
            }],
            'contacts': [
                {
                    'id': str(contact.pk),
                    'name': contact.name,
                    'first_name': contact.first_name,
                    'last_name': contact.last_name,
                    'job_title': contact.job_title,
                },
            ],
            'event': None,
            'service': {
                'id': str(Service.inbound_referral.value.id),
                'name': Service.inbound_referral.value.name,
            },
            'service_answers': None,
            'investment_project': request_data.get('investment_project'),
            'archived_documents_url_path': '',
            'were_countries_discussed': request_data.get('were_countries_discussed'),
            'export_countries': request_data.get('export_countries', []),
            'created_by': {
                'id': str(adviser.pk),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
            },
            'modified_by': {
                'id': str(adviser.pk),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'company_referral': None,
            'large_capital_opportunity': None,
            'has_related_trade_agreements': request_data.get(
                'has_related_trade_agreements', False,
            ),
            'related_trade_agreements': request_data.get(
                'related_trade_agreements', [],
            ),
        }

    @freeze_time('2017-04-18 13:25:30.986208')
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    def test_add_interaction_add_company_export_country(self, permissions):
        """
        Test add a new interaction with export country
        make sure it syncs across to company as a new entry.
        """
        adviser = create_test_user(
            permission_codenames=permissions,
            dit_team=TeamFactory(),
        )
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v4:interaction:collection')
        request_data = {
            'kind': Interaction.Kind.INTERACTION,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_participants': [
                {'adviser': adviser.pk},
            ],
            'company': company.pk,
            'contacts': [contact.pk],
            'service': Service.inbound_referral.value.id,
            'was_policy_feedback_provided': False,
            'theme': Interaction.Theme.EXPORT,
            'were_countries_discussed': True,
            'export_countries': [
                {
                    'country': {
                        'id': Country.canada.value.id,
                    },
                    'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                },
            ],
            'has_related_trade_agreements': False,
            'related_trade_agreements': [],
        }

        api_client = self.create_api_client(user=adviser)
        response = api_client.post(url, request_data)

        assert response.status_code == status.HTTP_201_CREATED

        export_countries = company.export_countries.all()
        assert export_countries.count() == 1
        assert str(export_countries[0].country.id) == Country.canada.value.id
        currently_exporting = CompanyExportCountry.Status.CURRENTLY_EXPORTING
        assert export_countries[0].status == currently_exporting

    @freeze_time('2017-04-18 13:25:30.986208')
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    @pytest.mark.parametrize(
        'export_country_date,interaction_date,expected_status',
        (
            # current dated interaction overriding existing older status
            (
                '2017-01-18',
                '2017-04-18',
                CompanyExportCountry.Status.CURRENTLY_EXPORTING,
            ),
            # past dated interaction can't override existing newer status
            (
                '2017-03-18',
                '2017-02-18',
                CompanyExportCountry.Status.NOT_INTERESTED,
            ),
            # future dated interaction, will be treated as current
            # and can't override existing much newer status
            (
                '2017-05-18',
                '2018-02-18',
                CompanyExportCountry.Status.NOT_INTERESTED,
            ),
            # future dated interaction, will be treated as current
            # and will override existing older status
            (
                '2017-03-18',
                '2018-02-18',
                CompanyExportCountry.Status.CURRENTLY_EXPORTING,
            ),
        ),
    )
    def test_add_interaction_update_company_export_country(
        self,
        permissions,
        export_country_date,
        interaction_date,
        expected_status,
    ):
        """
        Test add a new interaction with export country
        consolidates to company export countries.
        """
        adviser = create_test_user(
            permission_codenames=permissions,
            dit_team=TeamFactory(),
        )
        company = CompanyFactory()
        with freeze_time(export_country_date):
            company.export_countries.set(
                [
                    CompanyExportCountryFactory(
                        company=company,
                        country=meta_models.Country.objects.get(
                            id=Country.canada.value.id,
                        ),
                        status=CompanyExportCountry.Status.NOT_INTERESTED,
                    ),
                ],
            )
        contact = ContactFactory(company=company)
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v4:interaction:collection')
        request_data = {
            'date': interaction_date,
            'kind': Interaction.Kind.INTERACTION,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'dit_participants': [
                {'adviser': adviser.pk},
            ],
            'company': company.pk,
            'contacts': [contact.pk],
            'service': Service.inbound_referral.value.id,
            'was_policy_feedback_provided': False,
            'theme': Interaction.Theme.EXPORT,
            'were_countries_discussed': True,
            'export_countries': [
                {
                    'country': {
                        'id': Country.canada.value.id,
                    },
                    'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                },
            ],
            'has_related_trade_agreements': False,
            'related_trade_agreements': [],
        }

        api_client = self.create_api_client(user=adviser)
        response = api_client.post(url, request_data)

        assert response.status_code == status.HTTP_201_CREATED

        export_countries = company.export_countries.all()
        assert export_countries.count() == 1
        assert str(export_countries[0].country.id) == Country.canada.value.id
        assert export_countries[0].status == expected_status

    @pytest.mark.parametrize(
        'data,errors',
        (
            # required fields
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                },
                {
                    'contacts': ['This field is required.'],
                    'date': ['This field is required.'],
                    'dit_participants': ['This field is required.'],
                    'subject': ['This field is required.'],
                    'company': ['This field is required.'],
                    'was_policy_feedback_provided': ['This field is required.'],
                    'has_related_trade_agreements': ['This field is required.'],
                    'related_trade_agreements': ['This field is required.'],
                },
            ),
            # service required for complete interaction
            # required fields
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'communication_channel': partial(
                        random_obj_for_model, CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'service': ['This field is required.'],
                },
            ),
            # communication_channel required for complete interaction
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'was_policy_feedback_provided': False,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'communication_channel': ['This field is required.'],
                },
            ),
            # policy feedback fields required when policy feedback provided
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': True,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'policy_areas': ['This field is required.'],
                    'policy_feedback_notes': ['This field is required.'],
                    'policy_issue_types': ['This field is required.'],
                },
            ),
            # policy feedback fields cannot be blank when policy feedback provided
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': True,
                    'policy_areas': [],
                    'policy_feedback_notes': '',
                    'policy_issue_types': [],
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'policy_areas': ['This field is required.'],
                    'policy_feedback_notes': ['This field is required.'],
                    'policy_issue_types': ['This field is required.'],
                },
            ),
            # at least one trade agreements field required when there are related trade agreements
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'theme': Interaction.Theme.TRADE_AGREEMENT,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'has_related_trade_agreements': True,
                },
                {
                    'related_trade_agreements': ['This field is required.'],
                },
            ),
            # trade agreements field cannot be blank when there are related trade agreements
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'theme': Interaction.Theme.TRADE_AGREEMENT,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'has_related_trade_agreements': True,
                    'related_trade_agreements': [],
                },
                {
                    'related_trade_agreements': ['This field is required.'],
                },
            ),
            # were_countries_discussed can't be null for export interactions
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'theme': Interaction.Theme.EXPORT,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'was_policy_feedback_provided': False,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'were_countries_discussed': None,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'were_countries_discussed': ['This field is required.'],
                },
            ),
            # were_countries_discussed can't be null for other interactions
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'theme': Interaction.Theme.OTHER,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'were_countries_discussed': None,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'were_countries_discussed': ['This field is required.'],
                },
            ),
            # were_countries_discussed can't be missing for export/other interactions
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'theme': Interaction.Theme.EXPORT,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'were_countries_discussed': ['This field is required.'],
                },
            ),
            # were_countries_discussed can't be missing when sending export_countries
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'theme': Interaction.Theme.EXPORT,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'were_countries_discussed': None,
                    'export_countries': [
                        {
                            'country': {
                                'id': Country.canada.value.id,
                            },
                            'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                        },
                    ],
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'were_countries_discussed': ['This field is required.'],
                    'export_countries': [
                        'This field is only valid when countries were discussed.',
                    ],
                },
            ),
            # export_countries cannot be blank when were_countries_discussed is True
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'theme': Interaction.Theme.EXPORT,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'were_countries_discussed': True,
                    'export_countries': None,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'export_countries': ['This field may not be null.'],
                },
            ),
            # export_countries cannot have same country more than once for a company
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'theme': Interaction.Theme.EXPORT,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'were_countries_discussed': True,
                    'export_countries': [
                        {
                            'country': {
                                'id': Country.canada.value.id,
                            },
                            'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                        },
                        {
                            'country': {
                                'id': Country.canada.value.id,
                            },
                            'status': CompanyExportCountry.Status.FUTURE_INTEREST,
                        },
                    ],
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'non_field_errors': [
                        'A country that was discussed cannot be entered in multiple fields.',
                    ],
                },
            ),
            # export_countries must be fully formed. Status can't be missing
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'theme': Interaction.Theme.EXPORT,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'were_countries_discussed': True,
                    'export_countries': [
                        {
                            'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                        },
                    ],
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'export_countries': [{'country': ['This field is required.']}],
                },
            ),
            # export_countries must be fully formed. Country can't be missing
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'theme': Interaction.Theme.EXPORT,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'were_countries_discussed': True,
                    'export_countries': [
                        {
                            'country': {
                                'id': Country.canada.value.id,
                            },
                        },
                    ],
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'export_countries': [{'status': ['This field is required.']}],
                },
            ),
            # export_countries must be fully formed. status must be a valid choice
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'theme': Interaction.Theme.EXPORT,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'were_countries_discussed': True,
                    'export_countries': [
                        {
                            'country': {
                                'id': Country.canada.value.id,
                            },
                            'status': 'foobar',
                        },
                    ],
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'export_countries': [
                        {'status': ['"foobar" is not a valid choice.']},
                    ],
                },
            ),
            # export_countries must be fully formed. country ID must be a valid UUID
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'theme': Interaction.Theme.EXPORT,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'were_countries_discussed': True,
                    'export_countries': [
                        {
                            'country': {
                                'id': '1234',
                            },
                            'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                        },
                    ],
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'export_countries': [{'country': ['Must be a valid UUID.']}],
                },
            ),
            # export_countries must be fully formed. country UUID must be a valid Country
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'theme': Interaction.Theme.EXPORT,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'were_countries_discussed': True,
                    'export_countries': [
                        {
                            'country': {
                                'id': '4dee26c2-799d-49a8-a533-c30c595c942c',
                            },
                            'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                        },
                    ],
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'export_countries': [
                        {
                            'country': [
                                'Invalid pk "4dee26c2-799d-49a8-a533-c30c595c942c"'
                                ' - object does not exist.',
                            ],
                        },
                    ],
                },
            ),
            # export_countries cannot be set when were_countries_discussed is False
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'theme': Interaction.Theme.EXPORT,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'were_countries_discussed': False,
                    'export_countries': [
                        {
                            'country': {
                                'id': Country.canada.value.id,
                            },
                            'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                        },
                    ],
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'export_countries': [
                        'This field is only valid when countries were discussed.',
                    ],
                },
            ),
            # fields not allowed
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'notes': 'hello',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'has_related_trade_agreements': False,
                    'grant_amount_offered': '1111.11',
                    'net_company_receipt': '8888.11',
                    # fields not allowed
                    'is_event': True,
                    'event': EventFactory,
                    'service_delivery_status': partial(
                        random_obj_for_model,
                        ServiceDeliveryStatus,
                    ),
                    'policy_areas': [partial(random_obj_for_model, PolicyArea)],
                    'policy_feedback_notes': 'Policy feedback notes.',
                    'policy_issue_types': [
                        partial(random_obj_for_model, PolicyIssueType),
                    ],
                    'related_trade_agreements': [TradeAgreement.uk_japan.value.id],
                },
                {
                    'is_event': ['This field is only valid for service deliveries.'],
                    'event': ['This field is only valid for service deliveries.'],
                    'service_delivery_status': [
                        'This field is only valid for service deliveries.',
                    ],
                    'policy_areas': [
                        'This field is only valid when policy feedback has been provided.',
                    ],
                    'policy_feedback_notes': [
                        'This field is only valid when policy feedback has been provided.',
                    ],
                    'policy_issue_types': [
                        'This field is only valid when policy feedback has been provided.',
                    ],
                    'related_trade_agreements': [
                        'This field is only valid when there are related trade agreements.',
                    ],
                },
            ),
            # fields where None is not allowed
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'notes': 'hello',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    # fields where None is not allowed
                    'dit_participants': None,
                    'was_policy_feedback_provided': None,
                    'policy_feedback_notes': None,
                    'has_related_trade_agreements': None,
                    'related_trade_agreements': None,
                },
                {
                    'dit_participants': ['This field may not be null.'],
                    'was_policy_feedback_provided': ['This field may not be null.'],
                    'policy_feedback_notes': ['This field may not be null.'],
                    'has_related_trade_agreements': ['This field may not be null.'],
                    'related_trade_agreements': ['This field may not be null.'],
                },
            ),
            # no contradictory messages if event is None but and is_event is True
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'was_policy_feedback_provided': False,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'event': None,
                    'is_event': True,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'is_event': ['This field is only valid for service deliveries.'],
                },
            ),
            # no duplicate messages for event if provided and is_event is False
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'was_policy_feedback_provided': False,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'event': EventFactory,
                    'is_event': False,
                },
                {
                    'is_event': ['This field is only valid for service deliveries.'],
                    'event': ['This field is only valid for service deliveries.'],
                },
            ),
            # dit_participants cannot be empty list
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'service': Service.inbound_referral.value.id,
                    'was_policy_feedback_provided': False,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                    'dit_participants': [],
                },
                {
                    'dit_participants': {
                        api_settings.NON_FIELD_ERRORS_KEY: [
                            'This list may not be empty.',
                        ],
                    },
                },
            ),
            # status must be a valid choice
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {
                            'adviser': AdviserFactory,
                        },
                    ],
                    'service': Service.inbound_referral.value.id,
                    'was_policy_feedback_provided': False,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                    'status': 'foobar',
                },
                {
                    'status': ['"foobar" is not a valid choice.'],
                },
            ),
            # service must be without children
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {
                            'adviser': AdviserFactory,
                        },
                    ],
                    'service': Service.enquiry_or_referral_received.value.id,
                    'was_policy_feedback_provided': False,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    'service': [
                        'This field is valid for services without children services.',
                    ],
                },
            ),
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'was_policy_feedback_provided': False,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                    'status': None,
                },
                {
                    'status': ['This field may not be null.'],
                },
            ),
            # were_countries_discussed can't be true for investment theme
            (
                {
                    'theme': Interaction.Theme.INVESTMENT,
                    'kind': Interaction.Kind.INTERACTION,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.inbound_referral.value.id,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'was_policy_feedback_provided': False,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                    'were_countries_discussed': True,
                },
                {
                    'were_countries_discussed': [
                        "This value can't be selected for investment interactions.",
                    ],
                },
            ),
            # can't update company and companies at the same time
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': lambda: CompanyFactory(name='Martian Island'),
                    'companies': [CompanyFactory],
                    'contacts': [
                        lambda: ContactFactory(
                            company=Company.objects.get(name='Martian Island'),
                        ),
                    ],
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                    'dit_participants': [{'adviser': AdviserFactory}],
                    'service': Service.inbound_referral.value.id,
                    'was_policy_feedback_provided': False,
                    'has_related_trade_agreements': False,
                    'related_trade_agreements': [],
                },
                {
                    NON_FIELD_ERRORS: ['Only either a company or companies can be provided.'],
                },
            ),
        ),
    )
    def test_validation(self, data, errors):
        """Test validation errors."""
        data = resolve_data(data)
        url = reverse('api-v4:interaction:collection')
        response = self.api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == errors

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_restricted_user_can_add_associated_investment_project_interaction(self):
        """
        Test that a restricted user can add an interaction for an associated investment project.
        """
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        requester = create_test_user(
            permission_codenames=[
                InteractionPermission.add_associated_investmentproject,
            ],
            dit_team=project_creator.dit_team,  # same dit team as the project creator
        )
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        url = reverse('api-v4:interaction:collection')
        api_client = self.create_api_client(user=requester)
        response = api_client.post(
            url,
            data={
                'kind': Interaction.Kind.INTERACTION,
                'company': company.pk,
                'contacts': [contact.pk],
                'communication_channel': random_obj_for_model(CommunicationChannel).pk,
                'subject': 'whatever',
                'date': date.today().isoformat(),
                'dit_participants': [
                    {'adviser': requester.pk},
                ],
                'notes': 'hello',
                'investment_project': project.pk,
                'service': Service.inbound_referral.value.id,
                'was_policy_feedback_provided': False,
                'has_related_trade_agreements': False,
                'related_trade_agreements': [],
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['dit_participants'][0]['adviser']['id'] == str(
            requester.pk,
        )
        assert response_data['investment_project']['id'] == str(project.pk)
        assert response_data['modified_on'] == '2017-04-18T13:25:30.986208Z'
        assert response_data['created_on'] == '2017-04-18T13:25:30.986208Z'

    def test_restricted_user_cannot_add_non_associated_investment_project_interaction(
        self,
    ):
        """
        Test that a restricted user cannot add an interaction for a non-associated investment
        project.
        """
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        requester = create_test_user(
            permission_codenames=[
                InteractionPermission.add_associated_investmentproject,
            ],
            dit_team=TeamFactory(),  # different dit team from the project creator
        )
        url = reverse('api-v4:interaction:collection')
        api_client = self.create_api_client(user=requester)
        response = api_client.post(
            url,
            data={
                'kind': Interaction.Kind.INTERACTION,
                'company': CompanyFactory().pk,
                'contacts': [ContactFactory().pk],
                'communication_channel': random_obj_for_model(CommunicationChannel).pk,
                'subject': 'whatever',
                'date': date.today().isoformat(),
                'dit_participants': [
                    {'adviser': requester.pk},
                ],
                'notes': 'hello',
                'investment_project': project.pk,
                'service': Service.inbound_referral.value.id,
                'was_policy_feedback_provided': False,
                'has_related_trade_agreements': False,
                'related_trade_agreements': [],
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'investment_project': [
                "You don't have permission to add an interaction for this "
                'investment project.',
            ],
        }

    def test_restricted_user_cannot_add_company_interaction(self):
        """Test that a restricted user cannot add a company interaction."""
        requester = create_test_user(
            permission_codenames=[
                InteractionPermission.add_associated_investmentproject,
            ],
        )
        url = reverse('api-v4:interaction:collection')
        api_client = self.create_api_client(user=requester)
        response = api_client.post(
            url,
            data={
                'kind': Interaction.Kind.INTERACTION,
                'company': CompanyFactory().pk,
                'contacts': [ContactFactory().pk],
                'communication_channel': random_obj_for_model(CommunicationChannel).pk,
                'subject': 'whatever',
                'date': date.today().isoformat(),
                'dit_participants': [
                    {'adviser': requester.pk},
                ],
                'notes': 'hello',
                'service': Service.inbound_referral.value.id,
                'was_policy_feedback_provided': False,
                'has_related_trade_agreements': False,
                'related_trade_agreements': [],
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'investment_project': ['This field is required.'],
        }


class TestGetInteraction(APITestMixin):
    """Tests for the get interaction view."""

    @pytest.mark.parametrize(
        'factory',
        (
            CompanyInteractionFactory,
            CompanyInteractionFactoryWithPolicyFeedback,
            InvestmentProjectInteractionFactory,
            ExportCountriesInteractionFactory,
            CompanyReferralInteractionFactory,
        ),
    )
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_VIEW_PERMISSIONS)
    @freeze_time('2017-04-18 13:25:30.986208')
    def test_non_restricted_user_can_get_interaction(self, permissions, factory):
        """Test that a non-restricted user can get various types of interaction."""
        requester = create_test_user(permission_codenames=permissions)
        interaction = factory()
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        response_data['contacts'].sort(key=itemgetter('id'))
        response_data['dit_participants'].sort(key=lambda item: item['adviser']['id'])

        try:
            company_referral = interaction.company_referral
        except ObjectDoesNotExist:
            company_referral = None

        assert response_data == {
            'id': response_data['id'],
            'kind': Interaction.Kind.INTERACTION,
            'status': Interaction.Status.COMPLETE,
            'theme': interaction.theme,
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_areas': [
                {
                    'id': str(policy_area.pk),
                    'name': policy_area.name,
                }
                for policy_area in interaction.policy_areas.all()
            ],
            'policy_feedback_notes': interaction.policy_feedback_notes,
            'policy_issue_types': [
                {
                    'id': str(policy_issue_type.pk),
                    'name': policy_issue_type.name,
                }
                for policy_issue_type in interaction.policy_issue_types.all()
            ],
            'was_policy_feedback_provided': interaction.was_policy_feedback_provided,
            'communication_channel': {
                'id': str(interaction.communication_channel.pk),
                'name': interaction.communication_channel.name,
            },
            'subject': interaction.subject,
            'date': interaction.date.date().isoformat(),
            'dit_participants': [
                {
                    'adviser': {
                        'id': str(dit_participant.adviser.pk),
                        'first_name': dit_participant.adviser.first_name,
                        'last_name': dit_participant.adviser.last_name,
                        'name': dit_participant.adviser.name,
                    },
                    'team': {
                        'id': str(dit_participant.team.pk),
                        'name': dit_participant.team.name,
                    },
                }
                for dit_participant in interaction.dit_participants.order_by('pk')
            ],
            'notes': interaction.notes,
            'company': {
                'id': str(interaction.company.pk),
                'name': interaction.company.name,
            },
            'companies': [{
                'id': str(interaction.company.pk),
                'name': interaction.company.name,
            }],
            'contacts': [
                {
                    'id': str(contact.pk),
                    'name': contact.name,
                    'first_name': contact.first_name,
                    'last_name': contact.last_name,
                    'job_title': contact.job_title,
                }
                for contact in interaction.contacts.order_by('pk')
            ],
            'event': None,
            'service': {
                'id': str(Service.inbound_referral.value.id),
                'name': Service.inbound_referral.value.name,
            },
            'service_answers': None,
            'investment_project': {
                'id': str(interaction.investment_project.pk),
                'name': interaction.investment_project.name,
                'project_code': interaction.investment_project.project_code,
            }
            if interaction.investment_project
            else None,
            'archived_documents_url_path': interaction.archived_documents_url_path,
            'were_countries_discussed': interaction.were_countries_discussed,
            'export_countries': [
                {
                    'country': {
                        'id': str(export_country.country.id),
                        'name': export_country.country.name,
                    },
                    'status': export_country.status,
                }
                for export_country in interaction.export_countries.all()
            ],
            'created_by': {
                'id': str(interaction.created_by.pk),
                'first_name': interaction.created_by.first_name,
                'last_name': interaction.created_by.last_name,
                'name': interaction.created_by.name,
            },
            'modified_by': {
                'id': str(interaction.modified_by.pk),
                'first_name': interaction.modified_by.first_name,
                'last_name': interaction.modified_by.last_name,
                'name': interaction.modified_by.name,
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'company_referral': {
                'id': str(company_referral.pk),
                'subject': company_referral.subject,
                'created_by': format_expected_adviser(company_referral.created_by),
                'created_on': '2017-04-18T13:25:30.986208Z',
                'recipient': format_expected_adviser(company_referral.recipient),
            }
            if company_referral
            else None,
            'large_capital_opportunity': None,
            'has_related_trade_agreements': None,
            'related_trade_agreements': [],
        }

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_restricted_user_can_get_associated_investment_project_interaction(self):
        """Test that a restricted user can get an associated investment project interaction."""
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        interaction = InvestmentProjectInteractionFactory(investment_project=project)
        requester = create_test_user(
            permission_codenames=[
                InteractionPermission.view_associated_investmentproject,
            ],
            dit_team=project_creator.dit_team,
        )
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        response_data['contacts'].sort(key=itemgetter('id'))
        response_data['dit_participants'].sort(
            key=lambda dit_participant: dit_participant['adviser']['id'],
        )
        assert response_data == {
            'id': response_data['id'],
            'kind': Interaction.Kind.INTERACTION,
            'status': Interaction.Status.COMPLETE,
            'theme': interaction.theme,
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_areas': [],
            'policy_feedback_notes': '',
            'policy_issue_types': [],
            'was_policy_feedback_provided': False,
            'communication_channel': {
                'id': str(interaction.communication_channel.pk),
                'name': interaction.communication_channel.name,
            },
            'subject': interaction.subject,
            'date': interaction.date.date().isoformat(),
            'dit_participants': [
                {
                    'adviser': {
                        'id': str(dit_participant.adviser.pk),
                        'first_name': dit_participant.adviser.first_name,
                        'last_name': dit_participant.adviser.last_name,
                        'name': dit_participant.adviser.name,
                    },
                    'team': {
                        'id': str(dit_participant.team.pk),
                        'name': dit_participant.team.name,
                    },
                }
                for dit_participant in interaction.dit_participants.all()
            ],
            'notes': interaction.notes,
            'company': {
                'id': str(interaction.company.pk),
                'name': interaction.company.name,
            },
            'companies': [{
                'id': str(interaction.company.pk),
                'name': interaction.company.name,
            }],
            'contacts': [
                {
                    'id': str(contact.pk),
                    'name': contact.name,
                    'first_name': contact.first_name,
                    'last_name': contact.last_name,
                    'job_title': contact.job_title,
                }
                for contact in interaction.contacts.order_by('pk')
            ],
            'event': None,
            'service': {
                'id': str(Service.inbound_referral.value.id),
                'name': Service.inbound_referral.value.name,
            },
            'service_answers': None,
            'investment_project': {
                'id': str(interaction.investment_project.pk),
                'name': interaction.investment_project.name,
                'project_code': interaction.investment_project.project_code,
            },
            'were_countries_discussed': interaction.were_countries_discussed,
            'export_countries': [
                {
                    'country': {
                        'id': str(export_country.country.id),
                        'name': export_country.country.name,
                    },
                    'status': export_country.status,
                }
                for export_country in interaction.export_countries.all()
            ],
            'archived_documents_url_path': interaction.archived_documents_url_path,
            'created_by': {
                'id': str(interaction.created_by.pk),
                'first_name': interaction.created_by.first_name,
                'last_name': interaction.created_by.last_name,
                'name': interaction.created_by.name,
            },
            'modified_by': {
                'id': str(interaction.modified_by.pk),
                'first_name': interaction.modified_by.first_name,
                'last_name': interaction.modified_by.last_name,
                'name': interaction.modified_by.name,
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'company_referral': None,
            'large_capital_opportunity': None,
            'has_related_trade_agreements': None,
            'related_trade_agreements': [],
        }

    def test_restricted_user_cannot_get_non_associated_investment_project_interaction(
        self,
    ):
        """
        Test that a restricted user cannot get a non-associated investment project
        interaction.
        """
        interaction = InvestmentProjectInteractionFactory()
        requester = create_test_user(
            permission_codenames=[
                InteractionPermission.view_associated_investmentproject,
            ],
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_user_cannot_get_company_interaction(self):
        """Test that a restricted user cannot get a company interaction."""
        interaction = CompanyInteractionFactory()
        requester = create_test_user(
            permission_codenames=[
                InteractionPermission.view_associated_investmentproject,
            ],
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateInteraction(APITestMixin):
    """Tests for the update interaction view."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_CHANGE_PERMISSIONS)
    def test_non_restricted_user_can_update_interaction(self, permissions):
        """Test that a non-restricted user can update an interaction."""
        requester = create_test_user(permission_codenames=permissions)
        interaction = CompanyInteractionFactory(subject='I am a subject')

        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.patch(
            url,
            data={
                'subject': 'I am another subject',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'I am another subject'

    def test_restricted_user_cannot_update_company_interaction(self):
        """Test that a restricted user cannot update a company interaction."""
        requester = create_test_user(
            permission_codenames=[
                InteractionPermission.change_associated_investmentproject,
            ],
        )
        interaction = CompanyInteractionFactory(subject='I am a subject')

        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.patch(
            url,
            data={
                'subject': 'I am another subject',
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_user_cannot_update_non_associated_investment_project_interaction(
        self,
    ):
        """
        Test that a restricted user cannot update a non-associated investment project interaction.
        """
        interaction = InvestmentProjectInteractionFactory(
            subject='I am a subject',
        )
        requester = create_test_user(
            permission_codenames=[
                InteractionPermission.change_associated_investmentproject,
            ],
        )

        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.patch(
            url,
            data={
                'subject': 'I am another subject',
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_user_can_update_associated_investment_project_interaction(self):
        """
        Test that a restricted user can update an interaction for an associated investment project.
        """
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        interaction = CompanyInteractionFactory(
            subject='I am a subject',
            investment_project=project,
        )
        requester = create_test_user(
            permission_codenames=[
                InteractionPermission.change_associated_investmentproject,
            ],
            dit_team=project_creator.dit_team,
        )

        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.patch(
            url,
            data={
                'subject': 'I am another subject',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'I am another subject'

    @pytest.mark.parametrize(
        'initial_value,new_value',
        (
            (
                None,
                Interaction.Theme.EXPORT,
            ),
            (
                None,
                None,
            ),
        ),
    )
    def test_update_theme(self, initial_value, new_value):
        """Test that the theme field can be updated."""
        interaction = CompanyInteractionFactory(theme=initial_value)

        url = reverse('api-v4:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(
            url,
            data={
                'theme': new_value,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['theme'] == new_value

    def test_cannot_unset_theme(self):
        """Test that a theme can't be removed from an interaction."""
        interaction = CompanyInteractionFactory(theme=Interaction.Theme.EXPORT)

        url = reverse('api-v4:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(
            url,
            data={
                'theme': None,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'theme': ["A theme can't be removed once set."],
        }

    @pytest.mark.parametrize(
        'data,error_response',
        (
            (
                {
                    'status': Interaction.Status.COMPLETE,
                    'service': Service.inbound_referral.value.id,
                },
                {
                    'communication_channel': ['This field is required.'],
                },
            ),
            (
                {
                    'status': Interaction.Status.COMPLETE,
                    'communication_channel': partial(
                        random_obj_for_model,
                        CommunicationChannel,
                    ),
                },
                {
                    'service': ['This field is required.'],
                },
            ),
        ),
    )
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_CHANGE_PERMISSIONS)
    @freeze_time('2017-04-18 13:25:30.986208')
    def test_draft_update_enforces_required_fields(
        self, permissions, data, error_response,
    ):
        """
        Test that changing a draft to completed will enforce service and
        communication_channel to be set.
        """
        requester = create_test_user(permission_codenames=permissions)
        draft_interaction = CompanyInteractionFactory(
            kind=Interaction.Kind.INTERACTION,
            status=Interaction.Status.DRAFT,
            service_id=None,
            communication_channel=None,
        )
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:interaction:item', kwargs={'pk': draft_interaction.pk})
        data = resolve_data(data)
        response = api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == error_response

    @pytest.mark.parametrize(
        'data,error_response',
        (
            (
                {
                    'were_countries_discussed': False,
                },
                {
                    'were_countries_discussed': [
                        'This field is invalid for interaction updates.',
                    ],
                },
            ),
            (
                {
                    'were_countries_discussed': True,
                    'export_countries': [
                        {
                            'country': {
                                'id': Country.greece.value.id,
                            },
                            'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                        },
                    ],
                },
                {
                    'were_countries_discussed': [
                        'This field is invalid for interaction updates.',
                    ],
                    'export_countries': [
                        'This field is invalid for interaction updates.',
                    ],
                },
            ),
            (
                {
                    'export_countries': [
                        {
                            'country': {
                                'id': Country.greece.value.id,
                            },
                            'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                        },
                    ],
                },
                {
                    'export_countries': [
                        'This field is invalid for interaction updates.',
                    ],
                },
            ),
        ),
    )
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_CHANGE_PERMISSIONS)
    @pytest.mark.parametrize('flag', ((True, False)))
    @freeze_time('2017-04-18 13:25:30.986208')
    def test_clean_interaction_update_export_countries_validation_error(
        self,
        permissions,
        data,
        error_response,
        flag,
    ):
        """
        Test that a user can't update export countries in an interaction
        when the interaction doesn't have any export countries.
        """
        requester = create_test_user(permission_codenames=permissions)
        interaction = CompanyInteractionFactory(
            subject='I am a subject',
            theme=Interaction.Theme.EXPORT,
        )

        assert (
            len(Interaction.objects.get(pk=interaction.pk).export_countries.all()) == 0
        )

        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:interaction:item', kwargs={'pk': interaction.pk})
        data = resolve_data(data)
        response = api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == error_response

    @pytest.mark.parametrize(
        'data,error_response',
        (
            (
                {
                    'were_countries_discussed': False,
                },
                {
                    'were_countries_discussed': [
                        'This field is invalid for interaction updates.',
                    ],
                },
            ),
            (
                {
                    'were_countries_discussed': True,
                    'export_countries': [
                        {
                            'country': {
                                'id': Country.greece.value.id,
                            },
                            'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                        },
                    ],
                },
                {
                    'were_countries_discussed': [
                        'This field is invalid for interaction updates.',
                    ],
                    'export_countries': [
                        'This field is invalid for interaction updates.',
                    ],
                },
            ),
            (
                {
                    'export_countries': [
                        {
                            'country': {
                                'id': Country.greece.value.id,
                            },
                            'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                        },
                    ],
                },
                {
                    'export_countries': [
                        'This field is invalid for interaction updates.',
                    ],
                },
            ),
        ),
    )
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_CHANGE_PERMISSIONS)
    @pytest.mark.parametrize('flag', ((True, False)))
    @freeze_time('2017-04-18 13:25:30.986208')
    def test_update_export_countries_validation_error(
        self,
        permissions,
        data,
        error_response,
        flag,
    ):
        """
        Test that a user can't update export countries in an interaction
        when the interaction already has export countries set.
        """
        requester = create_test_user(permission_codenames=permissions)
        interaction = ExportCountriesInteractionFactory(
            export_countries__country_id=Country.canada.value.id,
            export_countries__status=CompanyExportCountry.Status.NOT_INTERESTED,
        )

        assert (
            len(Interaction.objects.get(pk=interaction.pk).export_countries.all()) > 0
        )

        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:interaction:item', kwargs={'pk': interaction.pk})
        data = resolve_data(data)
        response = api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == error_response

    @pytest.mark.parametrize('flag', ((True, False)))
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_CHANGE_PERMISSIONS)
    @freeze_time('2017-04-18 13:25:30.986208')
    def test_update_interaction_when_export_countries_set(self, permissions, flag):
        """
        Test that a user can update the interaction otherwise
        when the interaction already has export countries set
        """
        requester = create_test_user(permission_codenames=permissions)
        interaction = ExportCountriesInteractionFactory()

        assert (
            len(Interaction.objects.get(pk=interaction.pk).export_countries.all()) == 1
        )
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:interaction:item', kwargs={'pk': interaction.pk})
        data = {
            'subject': 'I am another subject',
        }
        data = resolve_data(data)
        response = api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'I am another subject'

    @freeze_time('2017-04-18 13:25:30.986208')
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    def test_add_interaction_with_company_export_country_check_history(
        self, permissions,
    ):
        """
        Test add a new interaction with export country
        check to make sure it is not tracked in company export country history.
        """
        adviser = create_test_user(
            permission_codenames=permissions, dit_team=TeamFactory(),
        )
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v4:interaction:collection')
        request_data = {
            'kind': Interaction.Kind.INTERACTION,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_participants': [
                {'adviser': adviser.pk},
            ],
            'company': company.pk,
            'contacts': [contact.pk],
            'service': Service.inbound_referral.value.id,
            'was_policy_feedback_provided': False,
            'theme': Interaction.Theme.EXPORT,
            'were_countries_discussed': True,
            'export_countries': [
                {
                    'country': {
                        'id': Country.canada.value.id,
                    },
                    'status': CompanyExportCountry.Status.CURRENTLY_EXPORTING,
                },
            ],
            'has_related_trade_agreements': True,
            'related_trade_agreements': ['50cf99fd-1150-421d-9e1c-b23750ebf5ca'],
        }

        api_client = self.create_api_client(user=adviser)
        response = api_client.post(url, request_data)

        assert response.status_code == status.HTTP_201_CREATED

        export_countries = company.export_countries.all()
        assert export_countries.count() == 1
        assert str(export_countries[0].country.id) == Country.canada.value.id
        currently_exporting = CompanyExportCountry.Status.CURRENTLY_EXPORTING
        assert export_countries[0].status == currently_exporting
        export_history = CompanyExportCountryHistory.objects.filter(
            company=company,
        )
        assert export_history.count() == 0


class TestListInteractions(APITestMixin):
    """Tests for the list interactions view."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_VIEW_PERMISSIONS)
    def test_non_restricted_user_can_only_list_relevant_interactions(self, permissions):
        """Test that a non-restricted user can list all interactions"""
        requester = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=requester)

        project = InvestmentProjectFactory()
        company = CompanyFactory()
        company_interactions = CompanyInteractionFactory.create_batch(
            3,
            company=company,
        )
        project_interactions = CompanyInteractionFactory.create_batch(
            3,
            investment_project=project,
        )

        url = reverse('api-v4:interaction:collection')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 6
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {
            str(i.id) for i in chain(project_interactions, company_interactions)
        }
        assert actual_ids == expected_ids

    def test_restricted_user_can_only_list_associated_interactions(self):
        """
        Test that a restricted user can only list interactions for associated investment
        projects.
        """
        creator = AdviserFactory()
        requester = create_test_user(
            permission_codenames=[
                InteractionPermission.view_associated_investmentproject,
            ],
            dit_team=creator.dit_team,
        )
        api_client = self.create_api_client(user=requester)

        company = CompanyFactory()
        non_associated_project = InvestmentProjectFactory()
        associated_project = InvestmentProjectFactory(created_by=creator)

        CompanyInteractionFactory.create_batch(3, company=company)
        CompanyInteractionFactory.create_batch(
            3,
            investment_project=non_associated_project,
        )
        associated_project_interactions = CompanyInteractionFactory.create_batch(
            2,
            investment_project=associated_project,
        )

        url = reverse('api-v4:interaction:collection')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 2
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in associated_project_interactions}
        assert actual_ids == expected_ids

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_VIEW_PERMISSIONS)
    def test_user_can_filter_by_large_capital_opportunities(self, permissions):
        """Test that a user can filter interactions by large capital opportunity."""
        requester = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=requester)

        opportunity = LargeCapitalOpportunityFactory()
        CompanyInteractionFactory.create_batch(3)
        opportunity_interactions = (
            LargeCapitalOpportunityInteractionFactory.create_batch(
                3,
                large_capital_opportunity=opportunity,
            )
        )
        url = reverse('api-v4:interaction:collection')
        response = api_client.get(
            url,
            {
                'large_capital_opportunity_id': opportunity.pk,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 3
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in opportunity_interactions}
        assert actual_ids == expected_ids
        for result in response_data['results']:
            assert result['large_capital_opportunity'] == {
                'id': str(opportunity.pk),
                'name': opportunity.name,
            }
