from rest_framework import serializers

from datahub.company.models import Company
from datahub.interaction.models import Interaction
from datahub.interaction.serializers import InteractionSerializerV4


class ActivityInteractionSerializer(InteractionSerializerV4):
    """Serializer for an interaction with only the data required for a company activity"""

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
        )


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

    def get_activities(self, company):
        """Gets all company activities (Interactions, Orders etc)"""
        interactions = self.get_interactions(company)

        activities = []
        activities += interactions

        return activities

    def get_interactions(self, company):
        """
        Returns all the interactions for the company.

        Also applies any filters from the query_params to the related models.
        """
        interactions = company.interactions

        advisers = self.get_adviser_from_post_data()

        if advisers:
            interactions = interactions.filter(
                dit_participants__adviser_id__in=advisers)

        date_before, date_after = self.get_dates_from_post_data()

        if date_before:
            interactions = interactions.filter(
                date__lte=date_before,
            )

        if date_after:
            interactions = interactions.filter(
                date__gte=date_after,
            )

        return ActivityInteractionSerializer(interactions, many=True).data

    def get_request_data(self):
        """Get the post request parameter data"""
        request = self.context.get('request')
        if not request:
            return {}
        return request.data

    def get_adviser_from_post_data(self):
        """Get the adviser from post data."""
        advisers = self.get_request_data().get('advisers')

        if not advisers or type(advisers) is not list:
            return []

        return advisers

    def get_dates_from_post_data(self):
        """Get the dates from post data."""
        request_data = self.get_request_data()
        date_before = request_data.get('date_before')
        date_after = request_data.get('date_after')

        return date_before, date_after


class CompanyActivityFilterSerializer(serializers.Serializer):
    advisers = serializers.ListField(
        child=serializers.UUIDField(), required=False)
    date_before = serializers.DateField(required=False)
    date_after = serializers.DateField(required=False)
