from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.settings import api_settings

from datahub.dnb_match.constants import NoMatchReason
from datahub.dnb_match.models import DnBMatchingResult
from datahub.dnb_match.utils import _get_list_of_latest_match_candidates


class SelectMatchingCandidateSerializer(serializers.Serializer):
    """DRF serializer for company match candidate selection."""

    duns_number = serializers.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        """Initialise the serializer with candidates data."""
        super().__init__(*args, **kwargs)

        company = self.context['company']

        self.context['candidates'] = _get_list_of_latest_match_candidates(company.pk)
        self.fields['duns_number'].choices = self._candidates_to_choices()

    def save(self):
        """Save matched candidate data into DnBMatchingResult."""
        for candidate in self.context['candidates']:
            if self.validated_data['duns_number'] == str(candidate.get('duns_number')):
                data = self._candidate_to_result(
                    candidate,
                    self.context['request'].user,
                )

                DnBMatchingResult.objects.update_or_create(
                    company=self.context['company'],
                    defaults={
                        'data': data,
                    },
                )

    def _candidates_to_choices(self):
        return [
            (str(candidate['duns_number']), candidate['name'])
            for candidate in self.context['candidates']
        ]

    @staticmethod
    def _candidate_to_result(candidate, adviser):
        """Transform matching candidate to matching result."""
        fields = (
            'duns_number',
            'name',
            'address_country',
            'global_ultimate_duns_number',
            'global_ultimate_name',
            'global_ultimate_country',
        )
        remap_key = {
            'address_country': 'country',
        }
        dnb_match = {
            remap_key.get(key, key): value for key, value in candidate.items() if key in fields
        }

        return {
            'dnb_match': dnb_match,
            'matched_by': 'adviser',
            'adviser': {
                'id': adviser.id,
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
            },
        }


class SelectNoMatchSerializer(serializers.Serializer):
    """DRF serializer for no match candidate selection."""

    default_error_messages = {
        'list_of_candidates_required': gettext_lazy(
            'List of candidates is required if the reason is "more_than_one".',
        ),
        'description_required': gettext_lazy(
            'The "description" is required if the reason is "other".',
        ),
        'too_many_fields': gettext_lazy(
            'If the reason is "not_listed" or "not_confident", other fields '
            'should not need to be filled.',
        ),
    }

    reason = serializers.ChoiceField(choices=NoMatchReason)

    description = serializers.CharField(required=False)
    candidates = serializers.ListField(child=serializers.CharField(), required=False)

    def save(self):
        """Save no match information to DnBMatchingResult."""
        data = self._get_request_data_to_result(self.context['request'].user)

        DnBMatchingResult.objects.update_or_create(
            company=self.context['company'],
            defaults={
                'data': data,
            },
        )

    def validate(self, data):
        """Check if correct fields are filled in."""
        self._check_reason_more_than_one(data)
        self._check_reason_other(data)
        self._check_reason_not_listed_or_not_confident(data)
        return data

    def _check_reason_more_than_one(self, data):
        """Check if the reason "more_than_one" has a list of candidates."""
        if data['reason'] == NoMatchReason.more_than_one and not data.get('candidates'):
            error = {
                'candidates': [
                    self.error_messages['list_of_candidates_required'],
                ],
            }
            raise serializers.ValidationError(error, code='list_of_candidates_required')

    def _check_reason_other(self, data):
        """Check if the reason "other" has a description."""
        if data['reason'] == NoMatchReason.other and not data.get('description'):
            error = {
                'description': [
                    self.error_messages['description_required'],
                ],
            }
            raise serializers.ValidationError(error, code='description_required')

    def _check_reason_not_listed_or_not_confident(self, data):
        """Check if the reason "not_listed" or "not_confident" does not have other fields."""
        reason_not_listed_or_not_confident = data['reason'] in (
            NoMatchReason.not_listed, NoMatchReason.not_confident,
        )
        other_fields_than_reason = data.keys() != {'reason'}

        if reason_not_listed_or_not_confident and other_fields_than_reason:
            error = {
                api_settings.NON_FIELD_ERRORS_KEY: [
                    self.error_messages['too_many_fields'],
                ],
            }
            raise serializers.ValidationError(error, code='too_many_fields')

    def _get_request_data_to_result(self, adviser):
        no_match = {
            'reason': self.validated_data['reason'],
        }
        if self.validated_data['reason'] == NoMatchReason.more_than_one:
            no_match['candidates'] = self.validated_data['candidates']
        if self.validated_data['reason'] == NoMatchReason.other:
            no_match['description'] = self.validated_data['description']

        return {
            'no_match': no_match,
            'matched_by': 'adviser',
            'adviser': {
                'id': adviser.id,
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
            },
        }
