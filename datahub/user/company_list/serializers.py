from rest_framework import serializers

from datahub.company.models import Company
from datahub.core.serializers import NestedRelatedField
from datahub.user.company_list.models import CompanyList, CompanyListItem


class CompanyListSerializer(serializers.ModelSerializer):
    """Serialiser for a company list."""

    # This is an annotation on the query set
    item_count = serializers.ReadOnlyField()

    class Meta:
        model = CompanyList
        fields = (
            'id',
            'item_count',
            'name',
            'created_on',
        )


class CompanyListItemSerializer(serializers.ModelSerializer):
    """Serialiser for company list items."""

    company = NestedRelatedField(
        Company,
        extra_fields=('archived', 'name', 'trading_names'),
    )
    latest_interaction = serializers.SerializerMethodField()

    def get_latest_interaction(self, obj):
        """
        Construct a latest interaction object from the latest_interaction_id,
        latest_interaction_date and latest_interaction_subject query set annotations.
        """
        if not obj.latest_interaction_id:
            return None

        return {
            'id': obj.latest_interaction_id,
            'created_on': obj.latest_interaction_created_on,
            # For consistency with the main interaction API, only return the date part.
            # See InteractionSerializer for more information
            'date': obj.latest_interaction_date.date(),
            'subject': obj.latest_interaction_subject,
            'dit_participants': obj.latest_interaction_dit_participants or [],
        }

    class Meta:
        model = CompanyListItem
        fields = (
            'company',
            'created_on',
            'latest_interaction',
        )
