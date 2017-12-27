from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.oauth.scopes import Scope
from datahub.search.contact.apps import ContactSearchApp
from datahub.search.contact.models import Contact
from datahub.search.elasticsearch import get_search_by_entity_query, limit_search_query
from datahub.search.interaction.apps import InteractionSearchApp
from datahub.search.interaction.models import Interaction
from datahub.search.permissions import has_permissions_for_app
from .serializers import HomepageSerializer


class IntelligentHomepageView(APIView):
    """Return the data for the intelligent homepage."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)

    required_scopes = (Scope.internal_front_end,)
    http_method_names = ['get']

    def get(self, request, format=None):
        """Implement GET method."""
        serializer = HomepageSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        limit = serializer.validated_data['limit']

        interactions = self._get_interactions(request, limit)
        contacts = self._get_contacts(request, limit)

        response = {
            'interactions': interactions,
            'contacts': contacts,
        }

        return Response(data=response)

    def _get_interactions(self, request, limit):
        if not has_permissions_for_app(request, InteractionSearchApp):
            return []

        interactions_query = get_search_by_entity_query(
            term='',
            entity=Interaction,
            filter_data={
                'dit_adviser.id': request.user.id,
                'created_on_exists': True,
            },
            field_order='created_on:desc',
        )
        interactions = limit_search_query(
            interactions_query,
            offset=0,
            limit=limit,
        ).execute()

        return [interaction.to_dict() for interaction in interactions.hits]

    def _get_contacts(self, request, limit):
        if not has_permissions_for_app(request, ContactSearchApp):
            return []

        contacts_query = get_search_by_entity_query(
            term='',
            entity=Contact,
            filter_data={
                'created_by.id': request.user.id,
                'created_on_exists': True,
            },
            field_order='created_on:desc',
        )
        contacts = limit_search_query(
            contacts_query,
            offset=0,
            limit=limit,
        ).execute()

        return [contact.to_dict() for contact in contacts.hits]
