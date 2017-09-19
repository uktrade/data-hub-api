from datetime import timedelta

from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.company.queryset import get_contact_queryset
from datahub.interaction.queryset import get_interaction_queryset_v1
from datahub.oauth.scopes import Scope

from .serializers import IntelligentHomepageSerializer


class IntelligentHomepageView(APIView):
    """Return the data for the intelligent homepage."""

    required_scopes = (Scope.internal_front_end,)
    http_method_names = ['get']

    def get(self, request, format=None):
        """Implement GET method."""
        user = request.user
        days = request.GET.get('days', 15)
        days_in_the_past = now() - timedelta(days=int(days))

        interactions = get_interaction_queryset_v1().filter(
            dit_adviser=user,
            created_on__gte=days_in_the_past
        ).order_by('-created_on')

        contacts = get_contact_queryset().filter(
            adviser=user,
            created_on__gte=days_in_the_past
        ).order_by('-created_on')

        serializer = IntelligentHomepageSerializer({
            'interactions': interactions,
            'contacts': contacts
        })
        return Response(data=serializer.data)
