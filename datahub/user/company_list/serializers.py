from rest_framework import serializers

from datahub.company.models import Advisor, Company
from datahub.core.serializers import NestedRelatedField
from datahub.user.company_list.models import CompanyListItem


class CompanyListItemSerializer(serializers.Serializer):
    """Serializer used for managing company list items."""

    adviser = NestedRelatedField(Advisor)
    company = NestedRelatedField(Company)

    def update_or_create(self):
        """Add a company to a list (if it isn't already on it)."""
        CompanyListItem.objects.update_or_create(
            defaults={
                'adviser': self.validated_data['adviser'],
                'company': self.validated_data['company'],
            },
        )
