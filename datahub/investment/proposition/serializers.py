from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField
from datahub.investment.proposition.models import Proposition
from datahub.investment.serializers import NestedInvestmentProjectField


class CreatePropositionSerializer(serializers.ModelSerializer):
    """Proposition serialiser for create endpoint."""

    investment_project = NestedInvestmentProjectField()
    adviser = NestedAdviserField()

    class Meta:
        model = Proposition
        fields = (
            'investment_project',
            'adviser',
            'deadline',
            'name',
            'scope',
        )
        extra_kwargs = {
            'deadline': {'required': True},
            'name': {'required': True},
            'scope': {'required': True}
        }


class CompleteOrAbandonPropositionSerializer(serializers.ModelSerializer):
    """Proposition serialiser for complete and abandon endpoint."""

    class Meta:
        model = Proposition
        fields = (
            'details',
        )
        extra_kwargs = {
            'details': {'required': True},
        }

    def complete(self):
        """Complete a proposition."""
        self.instance.complete(
            by=self.context['current_user'],
            details=self.validated_data['details']
        )
        return self.instance

    def abandon(self):
        """Abandon a proposition."""
        self.instance.abandon(
            by=self.context['current_user'],
            details=self.validated_data['details']
        )
        return self.instance


class PropositionSerializer(serializers.ModelSerializer):
    """Proposition serialiser for view only endpoints."""

    investment_project = NestedInvestmentProjectField()
    adviser = NestedAdviserField()
    created_by = NestedAdviserField()
    modified_by = NestedAdviserField()

    class Meta:
        model = Proposition
        fields = (
            'id',
            'investment_project',
            'adviser',
            'deadline',
            'status',
            'name',
            'scope',
            'details',
            'created_on',
            'created_by',
            'modified_on',
            'modified_by',
        )
        read_only_fields = fields
