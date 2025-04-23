import uuid

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, format_date_or_datetime
from datahub.hcsat.models import CustomerSatisfactionToolFeedback
from datahub.hcsat.test.factories import CustomerSatisfactionToolFeedbackFactory

pytestmark = pytest.mark.django_db


class TestCustomerSatisfactionToolFeedbackViews(APITestMixin):
    """Tests for the HCSAT feedback views."""

    # create/POST

    @pytest.mark.parametrize('was_useful_value', [True, False])
    def test_create_minimal_valid(self, was_useful_value):
        """Test creating a feedback entry with only required fields."""
        url = reverse('api-v4:hcsat:collection')
        data = {
            'url': 'https://test.com/page',
            'was_useful': was_useful_value,
        }

        response = self.api_client.post(url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        feedback_id = response_data['id']

        # assert core fields
        assert response_data['url'] == data['url']
        assert response_data['was_useful'] == data['was_useful']

        # assert default detailed fields
        assert response_data['did_not_find_what_i_wanted'] is None
        assert response_data['lacks_feature'] is None
        assert response_data['other_issues'] is None
        assert response_data['other_issues_detail'] == ''
        assert response_data['improvement_suggestion'] == ''

        # assert db state
        instance = CustomerSatisfactionToolFeedback.objects.get(pk=feedback_id)
        assert instance.url == data['url']
        assert instance.was_useful == data['was_useful']
        assert instance.did_not_find_what_i_wanted is None
        assert instance.other_issues_detail == ''
        assert instance.improvement_suggestion == ''

    def test_create_fails_if_detailed_fields_provided(self):
        """Test create fails if any detailed feedback field is provided."""
        url = reverse('api-v4:hcsat:collection')
        data = {
            'url': 'https://test.com/page',
            'was_useful': False,
            'lacks_feature': True,  # not allowed on create
            'improvement_suggestion': 'Needs more detail.',  # not allowed on create
        }
        response = self.api_client.post(url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        errors = response.json()

        assert 'non_field_errors' in errors
        assert isinstance(errors['non_field_errors'], list)
        assert len(errors['non_field_errors']) > 0
        assert isinstance(errors['non_field_errors'][0], str)

        assert 'Detailed feedback fields cannot be provided' in errors['non_field_errors'][0]

    def test_create_fails_if_required_fields_missing(self):
        """Test create fails if required fields (url, was_useful) are missing."""
        url = reverse('api-v4:hcsat:collection')

        data = {'url': 'https://test.com/page'}
        response = self.api_client.post(url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'was_useful' in response.json()
        assert response.json()['was_useful'][0] == 'This field is required.'

        data = {'was_useful': True}
        response = self.api_client.post(url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'url' in response.json()
        assert response.json()['url'][0] == 'This field is required.'

    @pytest.mark.parametrize('method', ['get', 'put', 'delete'])
    def test_unsupported_methods_on_collection(self, method):
        """Test GET, PUT, DELETE on the collection endpoint return 405."""
        url = reverse('api-v4:hcsat:collection')
        response = getattr(self.api_client, method)(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    # update/PATCH

    def test_update_nonexistent_pk(self):
        """Test updating a non-existent feedback entry."""
        url = reverse('api-v4:hcsat:item', kwargs={'pk': uuid.uuid4()})
        data = {'lacks_feature': True}
        response = self.api_client.patch(url, data=data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_valid_detailed_feedback(self):
        """Test updating detailed feedback when the initial feedback was 'not useful'."""
        instance = CustomerSatisfactionToolFeedbackFactory(was_useful=False)
        url = reverse('api-v4:hcsat:item', kwargs={'pk': instance.pk})

        patch_data = {
            'lacks_feature': True,
            'improvement_suggestion': 'Needs a better UI.',
            'other_issues': True,
            'other_issues_detail': 'It was slow.',
        }

        with freeze_time() as frozen_datetime:
            response = self.api_client.patch(url, data=patch_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data['id'] == str(instance.id)
        assert response_data['lacks_feature'] is True
        assert response_data['improvement_suggestion'] == 'Needs a better UI.'
        assert response_data['other_issues'] is True
        assert response_data['other_issues_detail'] == 'It was slow.'
        assert response_data['modified_on'] == format_date_or_datetime(frozen_datetime())

        instance.refresh_from_db()
        assert instance.lacks_feature is True
        assert instance.improvement_suggestion == 'Needs a better UI.'
        assert instance.other_issues is True
        assert instance.other_issues_detail == 'It was slow.'

        assert instance.url == response_data['url']
        assert instance.was_useful is False

    def test_update_fails_if_detailed_feedback_on_useful_feedback(self):
        """Test update fails if trying to add detailed feedback to a 'useful' feedback."""
        instance = CustomerSatisfactionToolFeedbackFactory(was_useful=True)
        url = reverse('api-v4:hcsat:item', kwargs={'pk': instance.pk})
        patch_data = {'lacks_feature': True}

        response = self.api_client.patch(url, data=patch_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        errors = response.json()

        assert 'non_field_errors' in errors
        assert 'Detailed feedback cannot be added' in errors['non_field_errors'][0]

    def test_update_fails_if_other_detail_without_other_flag(self):
        """Test update fails if other_issues_detail is provided but other_issues is false."""
        instance = CustomerSatisfactionToolFeedbackFactory(was_useful=False, other_issues=False)
        url = reverse('api-v4:hcsat:item', kwargs={'pk': instance.pk})
        patch_data = {'other_issues_detail': 'This should fail.'}

        response = self.api_client.patch(url, data=patch_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        errors = response.json()

        assert 'other_issues_detail' in errors
        assert 'Other issues detail can only be provided' in errors['other_issues_detail'][0]

    def test_update_succeeds_if_other_detail_with_other_flag_true(self):
        """Test update succeeds if other_issues_detail is provided and other_issues is true."""
        instance = CustomerSatisfactionToolFeedbackFactory(was_useful=False, other_issues=False)
        url = reverse('api-v4:hcsat:item', kwargs={'pk': instance.pk})
        patch_data = {
            'other_issues': True,
            'other_issues_detail': 'This should pass now.',
        }

        response = self.api_client.patch(url, data=patch_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['other_issues'] is True
        assert response_data['other_issues_detail'] == 'This should pass now.'

        instance.refresh_from_db()
        assert instance.other_issues is True
        assert instance.other_issues_detail == 'This should pass now.'

    def test_update_ignores_readonly_fields(self):
        """Test update ignores attempts to change read-only fields like url and was_useful."""
        instance = CustomerSatisfactionToolFeedbackFactory(was_useful=False)
        original_url = instance.url
        url = reverse('api-v4:hcsat:item', kwargs={'pk': instance.pk})

        patch_data = {
            'url': 'https://new-url.com/should-be-ignored',
            'was_useful': True,
            'improvement_suggestion': 'Allowed field change.',
        }

        response = self.api_client.patch(url, data=patch_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        # assert *no change* to read-only fields
        assert response_data['url'] == original_url
        assert response_data['was_useful'] is False

        # assert expected changes
        assert response_data['improvement_suggestion'] == 'Allowed field change.'

        instance.refresh_from_db()
        assert instance.url == original_url
        assert instance.was_useful is False
        assert instance.improvement_suggestion == 'Allowed field change.'

    @pytest.mark.parametrize('method', ['get', 'put', 'delete', 'post'])
    def test_unsupported_methods_on_item(self, method):
        """Test GET, PUT, DELETE, POST on the item endpoint return 405."""
        instance = CustomerSatisfactionToolFeedbackFactory()
        url = reverse('api-v4:hcsat:item', kwargs={'pk': instance.pk})
        response = getattr(self.api_client, method)(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
