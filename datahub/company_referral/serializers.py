from rest_framework import serializers

from datahub.company.serializers import NestedAdviserWithEmailAndTeamField
from datahub.company_referral.models import CompanyReferral
from datahub.core.serializers import NestedRelatedField


class CompanyReferralSerializer(serializers.ModelSerializer):
    """Serialiser for company referrals."""

    company = NestedRelatedField('company.Company')
    contact = NestedRelatedField('company.Contact', required=False, allow_null=True)
    completed_by = NestedAdviserWithEmailAndTeamField(read_only=True)
    created_by = NestedAdviserWithEmailAndTeamField(read_only=True)
    recipient = NestedAdviserWithEmailAndTeamField()

    class Meta:
        model = CompanyReferral
        fields = (
            'id',
            'company',
            'completed_by',
            'completed_on',
            'contact',
            'created_by',
            'created_on',
            'recipient',
            'status',
            'subject',
            'notes',
        )
        read_only_fields = (
            'id',
            'completed_on',
            'created_on',
            'status',
        )
