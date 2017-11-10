from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.company.queryset import get_contact_queryset
from datahub.interaction.queryset import get_interaction_queryset
from datahub.oauth.scopes import Scope

from .serializers import IntelligentHomepageSerializer, LimitParamSerializer


class IntelligentHomepageView(APIView):
    """Return the data for the intelligent homepage."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)

    required_scopes = (Scope.internal_front_end,)
    http_method_names = ['get']
    interaction_queryset = get_interaction_queryset().select_related(
        'contact__company',
        'investment_project__investor_company',
    )
    contact_queryset = get_contact_queryset()

    def get(self, request, format=None):
        """Implement GET method."""
        user = request.user
        serializer = LimitParamSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        limit = serializer.validated_data['limit']

        interactions = _filter_queryset(
            self.interaction_queryset.filter(dit_adviser=user),
            limit
        )

        contacts = _filter_queryset(
            self.contact_queryset.filter(created_by=user),
            limit
        )

        serializer = IntelligentHomepageSerializer({
            'interactions': interactions,
            'contacts': contacts
        })
        return Response(data=serializer.data)


def _filter_queryset(queryset, limit):
    return queryset.exclude(
        created_on=None
    ).order_by(
        '-created_on'
    )[:limit]
