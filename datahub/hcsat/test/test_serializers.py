from unittest import mock

import pytest

from datahub.hcsat.serializers import CustomerSatisfactionToolFeedbackSerializer
from datahub.hcsat.test.factories import CustomerSatisfactionToolFeedbackFactory

pytestmark = pytest.mark.django_db


def _get_request_mock(): return mock.Mock()


class TestCustomerSatisfactionToolFeedbackSerializer:
    """Tests for CustomerSatisfactionToolFeedbackSerializer."""

    def test_serialization(self):
        """Test serializing a feedback instance."""
        feedback = CustomerSatisfactionToolFeedbackFactory(
            was_useful=False,
            lacks_feature=True,
            improvement_suggestion='Add search.',
        )
        serializer = CustomerSatisfactionToolFeedbackSerializer(instance=feedback)

        expected_data = {
            'id': str(feedback.id),
            'url': feedback.url,
            'was_useful': feedback.was_useful,
            'did_not_find_what_i_wanted': feedback.did_not_find_what_i_wanted,
            'difficult_navigation': feedback.difficult_navigation,
            'lacks_feature': feedback.lacks_feature,
            'unable_to_load': feedback.unable_to_load,
            'inaccurate_information': feedback.inaccurate_information,
            'other_issues': feedback.other_issues,
            'other_issues_detail': feedback.other_issues_detail,
            'improvement_suggestion': feedback.improvement_suggestion,
            'created_on': feedback.created_on.isoformat().replace('+00:00', 'Z'),
            'modified_on': feedback.modified_on.isoformat().replace('+00:00', 'Z'),
        }

        # assert anonymity
        assert 'created_by' not in serializer.data
        assert serializer.data == expected_data

    # create/POST

    @pytest.mark.parametrize(
        'was_useful_value',
        [True, False],
    )
    def test_create_minimal_valid(self, was_useful_value):
        """Test creating a feedback entry with only required fields."""
        data = {
            'url': 'https://test.com/page',
            'was_useful': was_useful_value,
        }

        context = {'request': _get_request_mock(), 'view': mock.Mock(action='create')}
        serializer = CustomerSatisfactionToolFeedbackSerializer(data=data, context=context)

        assert serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        assert instance.url == data['url']
        assert instance.was_useful == data['was_useful']

        # assert detailed fields are defaults (none or '')
        assert instance.did_not_find_what_i_wanted is None
        assert instance.lacks_feature is None
        assert instance.other_issues_detail == ''
        assert instance.improvement_suggestion == ''

        # check no user is associated
        assert not hasattr(instance, 'created_by') or instance.created_by is None
        assert not hasattr(instance, 'modified_by') or instance.modified_by is None


    def test_create_fails_if_detailed_fields_provided(self):
        """Test create fails if any detailed feedback field is provided."""
        data = {
            'url': 'https://test.com/page',
            'was_useful': False,
            'lacks_feature': True, # this should not be allowed on create
            'improvement_suggestion': 'Needs more detail.', # this should not be allowed on create
        }
        context = {'request': _get_request_mock(), 'view': mock.Mock(action='create')}
        serializer = CustomerSatisfactionToolFeedbackSerializer(data=data, context=context)

        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        assert 'detailed_feedback_on_create' in serializer.errors['non_field_errors'][0].code


    def test_create_fails_if_required_fields_missing(self):
        """Test create fails if required fields (url, was_useful) are missing."""
        data = {'url': 'https://test.com/page'}
        context = {'request': _get_request_mock(), 'view': mock.Mock(action='create')}
        serializer = CustomerSatisfactionToolFeedbackSerializer(data=data, context=context)
        assert not serializer.is_valid()
        assert 'was_useful' in serializer.errors
        assert serializer.errors['was_useful'][0].code == 'required'

        data = {'was_useful': True}
        serializer = CustomerSatisfactionToolFeedbackSerializer(data=data, context=context)
        assert not serializer.is_valid()
        assert 'url' in serializer.errors
        assert serializer.errors['url'][0].code == 'required'

    # update/PATCH

    def test_update_valid_detailed_feedback(self):
        """Test updating detailed feedback when the initial feedback was 'not useful'."""
        instance = CustomerSatisfactionToolFeedbackFactory(was_useful=False)

        original_did_not_find = instance.did_not_find_what_i_wanted
        original_difficult_navigation = instance.difficult_navigation
        original_unable_to_load = instance.unable_to_load
        original_inaccurate_information = instance.inaccurate_information

        data = {
            'lacks_feature': True,
            'improvement_suggestion': 'Needs a better UI.',
            'other_issues': True,
            'other_issues_detail': 'It was slow.',
        }
        context = {'request': _get_request_mock(), 'view': mock.Mock(action='partial_update')}
        serializer = CustomerSatisfactionToolFeedbackSerializer(
            instance, data=data, partial=True, context=context,
        )

        assert serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        updated_instance.refresh_from_db()

        # assert fields that *were* updated
        assert updated_instance.lacks_feature is True
        assert updated_instance.improvement_suggestion == 'Needs a better UI.'
        assert updated_instance.other_issues is True
        assert updated_instance.other_issues_detail == 'It was slow.'

        # assert fields that *were not* updated
        assert updated_instance.did_not_find_what_i_wanted == original_did_not_find
        assert updated_instance.difficult_navigation == original_difficult_navigation
        assert updated_instance.unable_to_load == original_unable_to_load
        assert updated_instance.inaccurate_information == original_inaccurate_information

        # assert core fields are unchanged
        assert updated_instance.url == instance.url
        assert updated_instance.was_useful is False

    def test_update_fails_if_detailed_feedback_on_useful_feedback(self):
        """Test update fails if trying to add detailed feedback to a 'useful' feedback."""
        instance = CustomerSatisfactionToolFeedbackFactory(was_useful=True)

        data = {'lacks_feature': True}
        context = {'request': _get_request_mock(), 'view': mock.Mock(action='partial_update')}
        serializer = CustomerSatisfactionToolFeedbackSerializer(
            instance, data=data, partial=True, context=context,
        )

        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        assert 'detailed_feedback_on_useful_feedback' in serializer.errors['non_field_errors'][0].code

    def test_update_fails_if_other_detail_without_other_flag(self):
        """Test update fails if other_issues_detail is provided but other_issues is false."""
        instance = CustomerSatisfactionToolFeedbackFactory(was_useful=False, other_issues=False)

        data = {'other_issues_detail': 'This should fail.'}
        context = {'request': _get_request_mock(), 'view': mock.Mock(action='partial_update')}
        serializer = CustomerSatisfactionToolFeedbackSerializer(
            instance, data=data, partial=True, context=context,
        )

        assert not serializer.is_valid()
        assert 'other_issues_detail' in serializer.errors
        assert 'other_detail_without_other_selected' in serializer.errors['other_issues_detail'][0].code


    def test_update_succeeds_if_other_detail_with_other_flag_true(self):
        """Test update succeeds if other_issues_detail is provided and other_issues is true."""
        instance = CustomerSatisfactionToolFeedbackFactory(was_useful=False, other_issues=False)

        data = {
            'other_issues': True,
            'other_issues_detail': 'This should pass now.',
        }
        context = {'request': _get_request_mock(), 'view': mock.Mock(action='partial_update')}
        serializer = CustomerSatisfactionToolFeedbackSerializer(
            instance, data=data, partial=True, context=context,
        )

        assert serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        updated_instance.refresh_from_db()
        assert updated_instance.other_issues is True
        assert updated_instance.other_issues_detail == data['other_issues_detail']

    def test_update_fails_if_trying_to_change_url(self):
        """Test update ignores attempts to change the read-only URL field."""
        instance = CustomerSatisfactionToolFeedbackFactory(was_useful=False)
        original_url = instance.url
        data = {
            'url': 'https://new-url.com',
            'improvement_suggestion': 'Changing URL?',
        }
        context = {'request': _get_request_mock(), 'view': mock.Mock(action='partial_update')}
        serializer = CustomerSatisfactionToolFeedbackSerializer(
            instance, data=data, partial=True, context=context,
        )

        assert serializer.is_valid(raise_exception=True)

        updated_instance = serializer.save()
        updated_instance.refresh_from_db()

        # assert url has not changed from the original
        assert updated_instance.url == original_url

        # assert the other field was updated
        assert updated_instance.improvement_suggestion == 'Changing URL?'

    def test_update_fails_if_trying_to_change_was_useful(self):
        """Test update ignores attempts to change the read-only was_useful field."""
        instance = CustomerSatisfactionToolFeedbackFactory(was_useful=False)
        data = {
            'was_useful': True,
            'improvement_suggestion': 'Changing usefulness?',
        }
        context = {'request': _get_request_mock(), 'view': mock.Mock(action='partial_update')}
        serializer = CustomerSatisfactionToolFeedbackSerializer(
            instance, data=data, partial=True, context=context,
        )

        assert serializer.is_valid(raise_exception=True)

        updated_instance = serializer.save()
        updated_instance.refresh_from_db()

        # assert was_useful has not changed from the original false
        assert updated_instance.was_useful is False

        # assert the other field was updated
        assert updated_instance.improvement_suggestion == 'Changing usefulness?'
