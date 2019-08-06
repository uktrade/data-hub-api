from rest_framework import serializers

from datahub.company.models import Company
from datahub.core.serializers import PermittedFieldsModelSerializer
from datahub.interaction.models import InteractionPermission


class DNBMatchedCompanySerializer(PermittedFieldsModelSerializer):
    """
    Serialiser for data hub companies matched with a DNB entry.
    """

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
        }

    class Meta:
        model = Company
        fields = (
            'id',
            'latest_interaction',
        )
        permissions = {
            f'interaction.{InteractionPermission.view_all}': 'latest_interaction',
        }
