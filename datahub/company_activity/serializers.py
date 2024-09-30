from rest_framework import serializers
from rest_framework.pagination import LimitOffsetPagination

from datahub.company.models import Company
from datahub.company_referral.models import CompanyReferral
from datahub.company_referral.serializers import CompanyReferralSerializer
from datahub.interaction.models import Interaction
from datahub.interaction.serializers import InteractionSerializerV4


class ReferralInteractionSerializer(CompanyReferralSerializer):
    """Serialiser for all referral interactions in a company"""

    class Meta:
        model = CompanyReferral
        fields = (
            'completed_on',
            'created_on',
            'recipient',
            'created_by',
            'status',
            'subject',
            'notes',
        )


class ActivityInteractionSerializer(InteractionSerializerV4):
    """Serializer for an interaction with only the data required for a company activity"""

    activity_source = serializers.SerializerMethodField()
    company_referral = ReferralInteractionSerializer()

    class Meta:
        model = Interaction
        fields = (
            'id',
            'date',
            'subject',
            'contacts',
            'service',
            'dit_participants',
            'kind',
            'communication_channel',
            'activity_source',
            'company_referral',
        )

    def get_activity_source(self, interaction):
        """
        Returns the source of the activity.
        Used for the frontend to determine how to transform the data.

        For a referral interaction the source is 'referral'.
        """
        if hasattr(interaction, 'company_referral'):
            return 'referral'

        return 'interaction'


class CompanyActivitySerializer(serializers.ModelSerializer):
    """Serialiser for all activities in a company"""

    activities = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = (
            'trading_names',
            'name',
            'id',
            'activities',
        )
        read_only_fields = (
            'name',
            'id',
            'trading_names',
        )

    @staticmethod
    def get_interactions(company):
        """
        Returns all the interactions for the company.
        """
        return company.interactions.all().prefetch_related(
            'contacts',
            'service',
            'dit_participants__adviser',
            'dit_participants__team',
            'communication_channel',
            'company_referral',
            'company_referral__created_by',
            'company_referral__recipient',
        )

    def paginate_activities(self, activities):
        """Paginates the activities using limit and offset query params"""
        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(
            activities,
            self.context['request'],
        )
        data = ActivityInteractionSerializer(page, many=True).data
        return {
            'links': {
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link(),
            },
            'count': paginator.count,
            'results': data,
        }

    def get_activities(self, company):
        """Gets all company activities (Interactions, Orders etc)"""
        interactions = self.get_interactions(company)

        # Referrals are part of interactions once marked as complete, so
        # split referrals and interactions separately so they can be filtered
        # on their own fields.
        referrals = interactions.filter(company_referral__isnull=False)
        referrals = self.filter_queryset(
            referrals,
            'dit_participants__adviser_id__in',
            'company_referral__completed_on__lte',
            'company_referral__completed_on__gte',
        )
        # Remove referrals from interactions
        interactions = interactions.filter(company_referral__isnull=True)
        interactions = self.filter_queryset(
            interactions,
            'dit_participants__adviser_id__in',
            'date__lte',
            'date__gte',
        )

        activites = referrals | interactions
        activites = self.sort_queryset(activites)

        return self.paginate_activities(activites)

    def filter_queryset(
        self,
        queryset,
        adviser_field,
        date_before_field,
        date_after_field,
    ):
        """
        Filters the queryset for the given post data. Allows each queryset
        to specify their own filter fields.
        """
        advisers = self.get_adviser_from_post_data()

        if advisers:
            queryset = queryset.filter(
                **{adviser_field: advisers},
            )

        date_before, date_after = self.get_dates_from_post_data()
        if date_before:
            queryset = queryset.filter(
                **{date_before_field: date_before},
            )
        if date_after:
            queryset = queryset.filter(
                **{date_after_field: date_after},
            )

        return queryset

    def sort_queryset(self, queryset):
        """Returns the sorted queryset from the sort post data"""
        sortby = self.get_sortby_from_post_data()
        return queryset.order_by(sortby)

    def get_request_data(self):
        """Get the post request parameter data"""
        request = self.context.get('request')
        if not request:
            return {}
        return request.data

    def get_adviser_from_post_data(self):
        """Get the adviser from post data."""
        advisers = self.get_request_data().get('dit_participants__adviser')

        if not advisers or type(advisers) is not list:
            return []

        return advisers

    def get_dates_from_post_data(self):
        """Get the dates from post data."""
        request_data = self.get_request_data()
        date_before = request_data.get('date_before')
        date_after = request_data.get('date_after')

        return date_before, date_after

    def get_sortby_from_post_data(self):
        """Get the sortby string from post data."""
        request_data = self.get_request_data()
        match request_data.get('sortby'):
            case 'date:desc':
                return '-date'
            case 'date:asc':
                return 'date'
            case _:
                return '-date'


class CompanyActivityFilterSerializer(serializers.Serializer):
    advisers = serializers.ListField(
        child=serializers.UUIDField(), required=False)
    date_before = serializers.DateField(required=False)
    date_after = serializers.DateField(required=False)
