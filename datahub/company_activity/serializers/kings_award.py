from rest_framework import serializers

from datahub.company.models import Company
from datahub.company_activity.models import KingsAwardRecipient
from datahub.core.serializers import NestedRelatedField


class KingsAwardRecipientSerializer(serializers.ModelSerializer):
    """Read-only KingsAwardRecipient serializer."""

    company = NestedRelatedField(
        Company,
        read_only=True,
        extra_fields=('name',),
    )

    category = serializers.CharField(
        source='get_category_display',
        read_only=True,
    )

    class Meta:
        model = KingsAwardRecipient
        fields = read_only_fields = (
            'id',
            'company',
            'year_awarded',
            'category',
            'citation',
            'year_expired',
        )
