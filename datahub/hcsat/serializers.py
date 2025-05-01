from django.utils.translation import gettext_lazy
from rest_framework import serializers

from datahub.hcsat.models import CustomerSatisfactionToolFeedback


class CustomerSatisfactionToolFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for CustomerSatisfactionToolFeedback."""

    default_error_messages = {
        'detailed_feedback_on_useful_feedback': gettext_lazy(
            'Detailed feedback cannot be added to feedback marked as useful.',
        ),
        'other_detail_without_other_selected': gettext_lazy(
            'Other issues detail can only be provided when other_issues is true.',
        ),
    }

    url = serializers.URLField(required=True)
    was_useful = serializers.BooleanField(required=True)

    # detailed fields are not required for the initial feedback creation
    did_not_find_what_i_wanted = serializers.BooleanField(required=False, allow_null=True)
    difficult_navigation = serializers.BooleanField(required=False, allow_null=True)
    lacks_feature = serializers.BooleanField(required=False, allow_null=True)
    unable_to_load = serializers.BooleanField(required=False, allow_null=True)
    inaccurate_information = serializers.BooleanField(required=False, allow_null=True)
    other_issues = serializers.BooleanField(required=False, allow_null=True)
    other_issues_detail = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    improvement_suggestion = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    # read-only fields to return in the response
    created_on = serializers.DateTimeField(read_only=True)
    modified_on = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CustomerSatisfactionToolFeedback
        fields = (
            'id',
            'url',
            'was_useful',
            'did_not_find_what_i_wanted',
            'difficult_navigation',
            'lacks_feature',
            'unable_to_load',
            'inaccurate_information',
            'other_issues',
            'other_issues_detail',
            'improvement_suggestion',
            'created_on',
            'modified_on',
        )

        read_only_fields = ('id', 'created_on', 'modified_on')

    def validate(self, data):
        """Validate based on the operation (create/update)."""
        is_update = self.instance is not None

        detailed_fields = {
            'did_not_find_what_i_wanted',
            'difficult_navigation',
            'lacks_feature',
            'unable_to_load',
            'inaccurate_information',
            'other_issues',
            'other_issues_detail',
            'improvement_suggestion',
        }
        provided_detailed_fields = detailed_fields.intersection(data.keys())

        if is_update:
            if self.instance.was_useful and provided_detailed_fields:
                raise serializers.ValidationError(
                    self.error_messages['detailed_feedback_on_useful_feedback'],
                    code='detailed_feedback_on_useful_feedback',
                )
        elif provided_detailed_fields:
            raise serializers.ValidationError(
                'Detailed feedback fields cannot be provided during initial feedback creation.',
                code='detailed_feedback_on_create',
            )

        other_issues = data.get(
            'other_issues',
            getattr(self.instance, 'other_issues', None) if self.instance else None,
        )
        other_issues_detail = data.get('other_issues_detail', None)

        if not other_issues and other_issues_detail not in (None, ''):
            raise serializers.ValidationError(
                {
                    'other_issues_detail': self.error_messages[
                        'other_detail_without_other_selected'
                    ],
                },
                code='other_detail_without_other_selected',
            )

        return data

    def create(self, validated_data):
        detailed_fields_to_remove = [
            'did_not_find_what_i_wanted',
            'difficult_navigation',
            'lacks_feature',
            'unable_to_load',
            'inaccurate_information',
            'other_issues',
            'other_issues_detail',
            'improvement_suggestion',
        ]
        for field in detailed_fields_to_remove:
            validated_data.pop(field, None)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Explicitly remove fields that should be read-only during update."""
        # ensure these fields are *never* passed to the superclass update method
        validated_data.pop('url', None)
        validated_data.pop('was_useful', None)

        # let the default model serializer handle the rest
        return super().update(instance, validated_data)
