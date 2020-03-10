from datetime import datetime
from uuid import uuid4

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.company.test.utils import format_expected_adviser
from datahub.company_referral.models import CompanyReferral
from datahub.company_referral.test.factories import (
    ClosedCompanyReferralFactory,
    CompanyReferralFactory,
    CompleteCompanyReferralFactory,
)
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_date_or_datetime,
    random_obj_for_model,
    resolve_objects,
)
from datahub.event.test.factories import EventFactory
from datahub.interaction.models import CommunicationChannel, Interaction
from datahub.interaction.test.utils import random_service


FROZEN_DATETIME = datetime(2020, 1, 24, 16, 26, 50, tzinfo=utc)


def _complete_url(pk):
    return reverse('api-v4:company-referral:complete', kwargs={'pk': pk})


class TestCompleteCompanyReferral(APITestMixin):
    """
    Tests for the complete a company referral view.

    There is some overlap between these and the tests for adding an interaction. However,
    these are subtly different, as the company field is not required here, and the referral
    object is (of course) also updated.
    """

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        referral = CompanyReferralFactory()
        url = _complete_url(referral.pk)
        response = api_client.post(url, data={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['change_companyreferral'], status.HTTP_201_CREATED),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status, api_client):
        """Test that the expected status is returned depending on the permissions the user has."""
        user = create_test_user(permission_codenames=permission_codenames)
        api_client = self.create_api_client(user=user)

        referral = CompanyReferralFactory()
        url = _complete_url(referral.pk)
        request_data = _sample_valid_request_data(referral)

        response = api_client.post(url, data=request_data)
        assert response.status_code == expected_status

    def test_returns_404_for_non_existent_referral(self):
        """Test that a 404 is returned for a non-existent referral ID."""
        url = _complete_url(uuid4())
        response = self.api_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        'factory',
        (
            ClosedCompanyReferralFactory,
            CompleteCompanyReferralFactory,
        ),
    )
    def test_fails_if_referral_not_outstanding(self, factory):
        """Test that a an error is returned if the referral is closed or already complete."""
        referral = factory()
        url = _complete_url(referral.pk)

        request_data = _sample_valid_request_data(referral)
        response = self.api_client.post(url, data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'non_field_errors': [
                'This referral can’t be completed as it’s not in the outstanding status',
            ],
        }

    @pytest.mark.parametrize(
        'request_data,expected_response_data',
        (
            pytest.param(
                {},
                {
                    'contacts': ['This field is required.'],
                    'date': ['This field is required.'],
                    'dit_participants': ['This field is required.'],
                    'kind': ['This field is required.'],
                    'subject': ['This field is required.'],
                    'was_policy_feedback_provided': ['This field is required.'],
                },
                id='omitted-fields',
            ),
            pytest.param(
                {
                    'contacts': None,
                    'date': None,
                    'dit_participants': None,
                    'kind': None,
                    'subject': None,
                    'was_policy_feedback_provided': None,
                },
                {
                    'contacts': ['This field may not be null.'],
                    'date': ['This field may not be null.'],
                    'dit_participants': ['This field may not be null.'],
                    'kind': ['This field may not be null.'],
                    'subject': ['This field may not be null.'],
                    'was_policy_feedback_provided': ['This field may not be null.'],
                },
                id='non-null-fields',
            ),
            pytest.param(
                {
                    # These fields shouldn't be allowed to be blank
                    'kind': '',
                    'subject': '',

                    # Provide values for other required fields (so we don't get errors for them)
                    'was_policy_feedback_provided': False,
                    'date': '2020-01-01',
                    'contacts': [ContactFactory],
                    'dit_participants': [
                        {
                            'adviser': AdviserFactory,
                        },
                    ],
                },
                {
                    'kind': ['"" is not a valid choice.'],
                    'subject': ['This field may not be blank.'],
                },
                id='non-blank-fields',
            ),
            pytest.param(
                {
                    # These fields shouldn't be allowed to be empty
                    'contacts': [],
                    'dit_participants': [],

                    # Provide values for other required fields (so we don't get errors for them)
                    'kind': Interaction.Kind.INTERACTION,
                    'subject': 'Test subject',
                    'was_policy_feedback_provided': False,
                    'date': '2020-01-01',
                },
                {
                    'contacts': ['This list may not be empty.'],
                    'dit_participants': {
                        'non_field_errors': ['This list may not be empty.'],
                    },
                },
                id='non-empty-fields',
            ),
            pytest.param(
                {
                    # These fields shouldn't be allowed to be blank for interactions
                    'communication_channel': None,
                    'service': None,

                    # Fill in the standard fields to test interaction validation
                    'kind': Interaction.Kind.INTERACTION,
                    'subject': 'test subject',
                    'was_policy_feedback_provided': False,
                    'date': '2020-01-01',
                    'contacts': [ContactFactory],
                    'dit_participants': [
                        {
                            'adviser': AdviserFactory,
                        },
                    ],
                },
                {
                    'communication_channel': ['This field is required.'],
                    'service': ['This field is required.'],
                },
                id='interaction-non-blank-fields',
            ),
            pytest.param(
                {
                    # These fields shouldn't be allowed to be blank for service deliveries
                    'is_event': None,
                    'service': None,

                    # Fill in the standard fields to test interaction validation
                    'kind': Interaction.Kind.SERVICE_DELIVERY,
                    'subject': 'test subject',
                    'was_policy_feedback_provided': False,
                    'date': '2020-01-01',
                    'contacts': [ContactFactory],
                    'dit_participants': [
                        {
                            'adviser': AdviserFactory,
                        },
                    ],
                },
                {
                    'is_event': ['This field is required.'],
                    'service': ['This field is required.'],
                },
                id='service-delivery-non-blank-fields',
            ),
        ),
    )
    def test_body_validation(self, request_data, expected_response_data):
        """Test validation of the request body in various cases."""
        referral = CompanyReferralFactory()
        url = _complete_url(referral.pk)

        resolved_data = resolve_objects(request_data)
        response = self.api_client.post(url, data=resolved_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_response_data

    def test_updates_referral_status(self):
        """Test that the status of the referral is updated on success."""
        referral = CompanyReferralFactory()
        url = _complete_url(referral.pk)

        request_data = _sample_valid_request_data(referral)

        with freeze_time(FROZEN_DATETIME):
            response = self.api_client.post(url, data=request_data)

        assert response.status_code == status.HTTP_201_CREATED

        response_data = response.json()
        referral.refresh_from_db()
        interaction = referral.interaction
        assert response_data == {
            'id': response_data['id'],
            'kind': Interaction.Kind.INTERACTION.value,
            'status': Interaction.Status.COMPLETE.value,
            'theme': interaction.theme,
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_areas': [],
            'policy_feedback_notes': '',
            'policy_issue_types': [],
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
                'id': str(interaction.service.pk),
                'name': interaction.service.name,
            },
            'service_answers': None,
            'investment_project': None,
            'archived_documents_url_path': interaction.archived_documents_url_path,
            'were_countries_discussed': interaction.were_countries_discussed,
            'export_countries': [],
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
            'created_on': format_date_or_datetime(FROZEN_DATETIME),
            'modified_on': format_date_or_datetime(FROZEN_DATETIME),
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'company_referral': {
                'id': str(referral.pk),
                'subject': referral.subject,
                'created_by': format_expected_adviser(referral.created_by),
                'created_on': format_date_or_datetime(referral.created_on),
                'recipient': format_expected_adviser(referral.recipient),
            },
        }

        assert referral.status == CompanyReferral.Status.COMPLETE
        assert referral.completed_by == self.user
        assert referral.completed_on == FROZEN_DATETIME
        assert referral.modified_by == self.user
        assert referral.modified_on == FROZEN_DATETIME

    @pytest.mark.parametrize(
        'extra_data',
        (
            pytest.param(
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'communication_channel': lambda: random_obj_for_model(CommunicationChannel),
                },
                id='interaction',
            ),
            pytest.param(
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'communication_channel': lambda: random_obj_for_model(CommunicationChannel),
                    # Any company in the request body should be ignored
                    'company': CompanyFactory,
                },
                id='company-is-ignored',
            ),
            pytest.param(
                {
                    'kind': Interaction.Kind.SERVICE_DELIVERY,
                    'is_event': True,
                    'event': EventFactory,
                },
                id='service-delivery',
            ),
        ),
    )
    def test_creates_an_interaction(self, extra_data):
        """Test that an interaction is created on success."""
        referral = CompanyReferralFactory()
        url = _complete_url(referral.pk)

        contact = ContactFactory(company=referral.company)
        service = random_service()

        request_data = {
            'kind': Interaction.Kind.INTERACTION,
            'subject': 'test subject',
            'date': '2020-02-03',
            'dit_participants': [
                {'adviser': self.user},
            ],
            'contacts': [contact],
            'service': service,
            'was_policy_feedback_provided': False,
            **extra_data,
        }

        resolved_request_data = resolve_objects(request_data)

        with freeze_time(FROZEN_DATETIME):
            response = self.api_client.post(url, data=resolved_request_data)

        assert response.status_code == status.HTTP_201_CREATED

        referral.refresh_from_db()

        assert referral.interaction_id
        interaction_data = Interaction.objects.values().get(pk=referral.interaction_id)
        assert interaction_data == {
            # Automatically set fields
            'company_id': referral.company_id,
            'created_by_id': self.user.pk,
            'created_on': FROZEN_DATETIME,
            'id': referral.interaction_id,
            'modified_by_id': self.user.pk,
            'modified_on': FROZEN_DATETIME,

            # Fields specified in the request body
            'communication_channel_id': resolved_request_data.get('communication_channel'),
            'date': datetime(2020, 2, 3, tzinfo=utc),
            'event_id': resolved_request_data.get('event'),
            'grant_amount_offered': None,
            'investment_project_id': None,
            'kind': resolved_request_data['kind'],
            'net_company_receipt': None,
            'notes': '',
            'policy_feedback_notes': '',
            'service_answers': None,
            'service_delivery_status_id': None,
            'service_id': service.pk,
            'source': None,
            'status': Interaction.Status.COMPLETE,
            'subject': resolved_request_data['subject'],
            'theme': None,
            'was_policy_feedback_provided': resolved_request_data['was_policy_feedback_provided'],
            'were_countries_discussed': None,

            # Other fields
            'archived': False,
            'archived_by_id': None,
            'archived_documents_url_path': '',
            'archived_on': None,
            'archived_reason': None,
        }

        assert list(referral.interaction.contacts.all()) == [contact]

        participant = referral.interaction.dit_participants.get()
        assert participant.adviser == self.user
        assert participant.team == self.user.dit_team


def _sample_valid_request_data(referral):
    adviser = AdviserFactory()
    contact = ContactFactory(company=referral.company)
    communication_channel = random_obj_for_model(CommunicationChannel)
    service = random_service()

    return {
        'kind': Interaction.Kind.INTERACTION,
        'communication_channel': communication_channel.pk,
        'subject': 'test subject',
        'date': '2020-02-03',
        'dit_participants': [
            {'adviser': adviser.pk},
        ],
        'contacts': [contact.pk],
        'service': service.pk,
        'was_policy_feedback_provided': False,
    }
