from django.utils.translation import gettext_lazy
from rest_framework import serializers

from datahub.company.models import Company
from datahub.core.serializers import NestedRelatedField
from datahub.user.company_list.models import CompanyList, CompanyListItem, PipelineItem

CANT_ADD_ARCHIVED_COMPANY_TO_PIPELINE_MESSAGE = gettext_lazy(
    "An archived company can't be added to the pipeline.",
)
COMPANY_ALREADY_EXISTS_IN_PIPELINE_MESSAGE = gettext_lazy(
    'This company already exists in the pipeline for this user.',
)


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
        # If this list of fields is changed, update the equivalent list in the QuerySet.only()
        # call in the queryset module
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


class PipelineItemSerializer(serializers.ModelSerializer):
    """Serialiser for pipeline item."""

    company = NestedRelatedField(
        Company,
        # If this list of fields is changed, update the equivalent list in the QuerySet.only()
        # call in the queryset module
        extra_fields=('name', 'turnover', 'export_potential'),
    )
    adviser = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate_company(self, company):
        """Make sure company is not archived"""
        if company.archived:
            raise serializers.ValidationError(CANT_ADD_ARCHIVED_COMPANY_TO_PIPELINE_MESSAGE)

        return company

    class Meta:
        model = PipelineItem
        fields = (
            'id',
            'company',
            'name',
            'status',
            'adviser',
            'created_on',
        )
        read_only_fields = (
            'id',
            'adviser',
            'created_on',
        )
