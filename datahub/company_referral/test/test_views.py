from collections.abc import Mapping
from datetime import datetime
from unittest.mock import ANY
from uuid import UUID, uuid4

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.company_referral.models import CompanyReferral
from datahub.company_referral.test.factories import CompanyReferralFactory
from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime

FROZEN_DATETIME = datetime(2020, 1, 24, 16, 26, 50, tzinfo=utc)

collection_url = reverse('api-v4:company-referral:collection')


def _item_url(pk):
    return reverse('api-v4:company-referral:item', kwargs={'pk': pk})


class TestListCompanyListsView(APITestMixin):
    """Tests for listing user's referrals."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        response = api_client.get(collection_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['view_companyreferral'], status.HTTP_200_OK),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status, api_client):
        """Test that the expected status is returned for various user permissions."""
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)
        api_client = self.create_api_client(user=user)
        response = api_client.get(collection_url)
        assert response.status_code == expected_status

    def test_returns_empty_list_when_no_lists(self):
        """Test that no results are returned when the user has no referrals."""
        response = self.api_client.get(collection_url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['results'] == []

    def test_doesnt_return_other_users_referrals(self):
        """Test that other users' referrals are not returned."""
        # Create some referrals sent or received by other users
        CompanyReferralFactory.create_batch(2)

        response = self.api_client.get(collection_url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['results'] == []

    def test_returns_items_in_expected_format(self):
        """Test that referrals are returned in expected format."""
        company_referral = CompanyReferralFactory(created_by=self.user)

        response = self.api_client.get(collection_url)
        assert response.status_code == status.HTTP_200_OK

        results = response.json()['results']
        assert len(results) == 1
        assert results[0] == {
            'id': str(company_referral.pk),
            'company': {
                'id': str(company_referral.company.pk),
                'name': company_referral.company.name,
            },
            'completed_on': format_date_or_datetime(company_referral.completed_on),
            'contact': {
                'id': str(company_referral.contact.pk),
                'name': company_referral.contact.name,
            },
            'created_by': {
                'id': str(company_referral.created_by.pk),
                'name': company_referral.created_by.name,
                'contact_email': company_referral.created_by.contact_email,
                'dit_team': {
                    'id': str(company_referral.created_by.dit_team.pk),
                    'name': company_referral.created_by.dit_team.name,
                },
            },
            'created_on': format_date_or_datetime(company_referral.created_on),
            'recipient': {
                'id': str(company_referral.recipient.pk),
                'name': company_referral.recipient.name,
                'contact_email': company_referral.recipient.contact_email,
                'dit_team': {
                    'id': str(company_referral.recipient.dit_team.id),
                    'name': company_referral.recipient.dit_team.name,
                },
            },
            'status': company_referral.status,
            'subject': company_referral.subject,
            'notes': company_referral.notes,
        }

    def test_returns_items_for_sender_and_recipient(self):
        """Test that both sent and received referrals are returned."""
        sender = CompanyReferralFactory(created_by=self.user)
        recipient1 = CompanyReferralFactory(recipient=self.user)
        recipient2 = CompanyReferralFactory(recipient=self.user)

        response = self.api_client.get(collection_url)
        assert response.status_code == status.HTTP_200_OK

        results = response.json()['results']
        assert len(results) == 3

        expected_referrals = {str(sender.pk), str(recipient1.pk), str(recipient2.pk)}
        assert {result['id'] for result in results} == expected_referrals


class TestAddCompanyReferral(APITestMixin):
    """Tests for the add company referral view."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        response = api_client.post(collection_url, data={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['add_companyreferral'], status.HTTP_201_CREATED),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status, api_client):
        """
        Test that the expected status is returned depending on the permissions the user has.
        """
        user = create_test_user(permission_codenames=permission_codenames)
        api_client = self.create_api_client(user=user)

        request_data = {
            'subject': 'Test referral',
            'company': {
                'id': CompanyFactory().pk,
            },
            'recipient': {
                'id': AdviserFactory().pk,
            },
        }

        response = api_client.post(collection_url, data=request_data)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        'request_data,expected_response_data',
        (
            pytest.param(
                {},
                {
                    'company': ['This field is required.'],
                    'recipient': ['This field is required.'],
                    'subject': ['This field is required.'],
                },
                id='omitted-fields',
            ),
            pytest.param(
                {
                    'company': None,
                    'notes': None,
                    'recipient': None,
                    'subject': None,
                },
                {
                    'company': ['This field may not be null.'],
                    'notes': ['This field may not be null.'],
                    'recipient': ['This field may not be null.'],
                    'subject': ['This field may not be null.'],
                },
                id='non-null-fields',
            ),
            pytest.param(
                {
                    # The value this field shouldn't be allowed to be an empty string
                    'subject': '',

                    # Provide values for other required fields (so we don't get errors for them)
                    'company': {
                        'id': CompanyFactory,
                    },
                    'recipient': {
                        'id': AdviserFactory,
                    },
                },
                {
                    'subject': ['This field may not be blank.'],
                },
                id='non-blank-fields',
            ),
        ),
    )
    def test_validates_input(self, request_data, expected_response_data):
        """Test validation for various scenarios."""
        resolved_request_data = _resolve_data(request_data)
        response = self.api_client.post(collection_url, data=resolved_request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_response_data

    @freeze_time(FROZEN_DATETIME)
    def test_can_create_a_referral_without_optional_fields(self):
        """Test that a referral can be created without optional values filled in."""
        company = CompanyFactory()
        recipient = AdviserFactory()
        subject = 'Test referral'

        request_data = {
            'subject': subject,
            'company': {
                'id': company.pk,
            },
            'recipient': {
                'id': recipient.pk,
            },
        }

        response = self.api_client.post(collection_url, data=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'company': {
                'id': str(company.pk),
                'name': company.name,
            },
            'completed_on': None,
            'contact': None,
            'created_by': {
                'contact_email': self.user.contact_email,
                'dit_team': {
                    'id': str(self.user.dit_team.pk),
                    'name': self.user.dit_team.name,
                },
                'id': str(self.user.pk),
                'name': self.user.name,
            },
            'created_on': format_date_or_datetime(FROZEN_DATETIME),
            'id': ANY,
            'notes': '',
            'recipient': {
                'contact_email': recipient.contact_email,
                'dit_team': {
                    'id': str(recipient.dit_team.pk),
                    'name': recipient.dit_team.name,
                },
                'id': str(recipient.pk),
                'name': recipient.name,
            },
            'status': CompanyReferral.STATUSES.outstanding,
            'subject': subject,
        }

    @freeze_time(FROZEN_DATETIME)
    def test_can_create_a_referral_with_optional_fields(self):
        """Test that a referral can be created with all optional values filled in."""
        company = CompanyFactory()
        contact = ContactFactory()
        recipient = AdviserFactory()
        subject = 'Test referral'
        notes = 'Some notes'

        request_data = {
            'subject': subject,
            'company': {
                'id': company.pk,
            },
            'recipient': {
                'id': recipient.pk,
            },
            'contact': {
                'id': contact.pk,
            },
            'notes': notes,
        }

        response = self.api_client.post(collection_url, data=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'company': {
                'id': str(company.pk),
                'name': company.name,
            },
            'completed_on': None,
            'contact': {
                'id': str(contact.pk),
                'name': contact.name,
            },
            'created_by': {
                'contact_email': self.user.contact_email,
                'dit_team': {
                    'id': str(self.user.dit_team.pk),
                    'name': self.user.dit_team.name,
                },
                'id': str(self.user.pk),
                'name': self.user.name,
            },
            'created_on': format_date_or_datetime(FROZEN_DATETIME),
            'id': ANY,
            'notes': notes,
            'recipient': {
                'contact_email': recipient.contact_email,
                'dit_team': {
                    'id': str(recipient.dit_team.pk),
                    'name': recipient.dit_team.name,
                },
                'id': str(recipient.pk),
                'name': recipient.name,
            },
            'status': CompanyReferral.STATUSES.outstanding,
            'subject': subject,
        }

    @freeze_time(FROZEN_DATETIME)
    def test_persists_data_to_the_database(self):
        """Test that created referrals are saved to the database."""
        request_data = {
            'subject': 'Test referral',
            'company': {
                'id': CompanyFactory().pk,
            },
            'contact': {
                'id': ContactFactory().pk,
            },
            'notes': 'Test notes',
            'recipient': {
                'id': AdviserFactory().pk,
            },
        }

        response = self.api_client.post(collection_url, data=request_data)
        assert response.status_code == status.HTTP_201_CREATED

        pk = response.json()['id']
        referral_data = CompanyReferral.objects.values().get(pk=pk)

        assert referral_data == {
            'company_id': request_data['company']['id'],
            'completed_by_id': None,
            'completed_on': None,
            'contact_id': request_data['contact']['id'],
            'created_by_id': self.user.pk,
            'created_on': FROZEN_DATETIME,
            'id': UUID(pk),
            'modified_by_id': self.user.pk,
            'modified_on': FROZEN_DATETIME,
            'notes': request_data['notes'],
            'recipient_id': request_data['recipient']['id'],
            'status': CompanyReferral.STATUSES.outstanding,
            'subject': request_data['subject'],
        }


class TestGetCompanyReferral(APITestMixin):
    """Tests for the get company referral view."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        referral = CompanyReferralFactory()
        url = _item_url(referral.pk)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['view_companyreferral'], status.HTTP_200_OK),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status, api_client):
        """
        Test that the expected status is returned depending on the permissions the user has.
        """
        referral = CompanyReferralFactory()
        user = create_test_user(permission_codenames=permission_codenames)

        url = _item_url(referral.pk)
        api_client = self.create_api_client(user=user)

        response = api_client.get(url)
        assert response.status_code == expected_status

    def test_returns_404_for_non_existent_referral(self):
        """Test that a 404 is returned for a non-existent referral ID."""
        url = _item_url(uuid4())
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_a_referral(self):
        """Test that a single referral can be retrieved."""
        referral = CompanyReferralFactory()
        url = _item_url(referral.pk)

        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'company': {
                'id': str(referral.company.pk),
                'name': referral.company.name,
            },
            'completed_on': None,
            'contact': {
                'id': str(referral.contact.pk),
                'name': referral.contact.name,
            },
            'created_by': {
                'contact_email': referral.created_by.contact_email,
                'dit_team': {
                    'id': str(referral.created_by.dit_team.pk),
                    'name': referral.created_by.dit_team.name,
                },
                'id': str(referral.created_by.pk),
                'name': referral.created_by.name,
            },
            'created_on': format_date_or_datetime(referral.created_on),
            'id': str(referral.pk),
            'notes': referral.notes,
            'recipient': {
                'contact_email': referral.recipient.contact_email,
                'dit_team': {
                    'id': str(referral.recipient.dit_team.pk),
                    'name': referral.recipient.dit_team.name,
                },
                'id': str(referral.recipient.pk),
                'name': referral.recipient.name,
            },
            'status': referral.status,
            'subject': referral.subject,
        }


def _resolve_data(data):
    """Resolve callables in values used in parametrised tests."""
    if isinstance(data, Mapping):
        return {key: _resolve_data(value) for key, value in data.items()}

    if callable(data):
        resolved_value = data()
    else:
        resolved_value = data

    return getattr(resolved_value, 'pk', resolved_value)
