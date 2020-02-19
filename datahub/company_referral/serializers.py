from django.db import transaction
from django.utils.translation import gettext_lazy
from rest_framework import serializers

from datahub.company.serializers import NestedAdviserWithEmailAndTeamField
from datahub.company_referral.models import CompanyReferral
from datahub.core.serializers import NestedRelatedField
from datahub.interaction.serializers import InteractionSerializer


class CompanyReferralSerializer(serializers.ModelSerializer):
    """Serialiser for company referrals."""

    company = NestedRelatedField('company.Company')
    contact = NestedRelatedField('company.Contact', required=False, allow_null=True)
    closed_by = NestedAdviserWithEmailAndTeamField(read_only=True)
    interaction = NestedRelatedField(
        'interaction.Interaction',
        read_only=True,
        extra_fields=('subject',),
    )
    completed_by = NestedAdviserWithEmailAndTeamField(read_only=True)
    created_by = NestedAdviserWithEmailAndTeamField(read_only=True)
    recipient = NestedAdviserWithEmailAndTeamField()

    class Meta:
        model = CompanyReferral
        fields = (
            'id',
            'closed_by',
            'closed_on',
            'company',
            'completed_by',
            'completed_on',
            'contact',
            'created_by',
            'created_on',
            'interaction',
            'notes',
            'recipient',
            'status',
            'subject',
        )
        read_only_fields = (
            'id',
            'closed_on',
            'completed_on',
            'created_on',
            'status',
        )


class CompleteCompanyReferralSerializer(InteractionSerializer):
    """Serialiser for the complete a referral view."""

    default_error_messages = {
        'invalid_status': gettext_lazy(
            'This referral can’t be completed as it’s not in the outstanding status',
        ),
    }

    def validate(self, data):
        """
        Validate provided data.

        Checks that the referral has the expected status.
        """
        referral = self.context['referral']
        if referral.status != CompanyReferral.Status.OUTSTANDING:
            raise serializers.ValidationError(self.error_messages['invalid_status'])

        return super().validate(data)

    @transaction.atomic
    def save(self):
        """Create an interaction and update the referral object."""
        referral = self.context['referral']
        user = self.context['user']

        interaction = super().save(created_by=user, modified_by=user)
        referral.mark_as_complete(interaction, user)
        referral.save()
