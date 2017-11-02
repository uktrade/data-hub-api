from datahub.core.permissions import UserHasPermissions
from datahub.oauth.scopes import Scope
from .models import Event
from .serializers import SearchEventSerializer
from ..views import SearchAPIView, SearchExportAPIView


class SearchEventParams:
    """Search event params."""

    required_scopes = (Scope.internal_front_end,)
    entity = Event
    serializer_class = SearchEventSerializer

    FILTER_FIELDS = (
        'address_country',
        'disabled_on_exists',
        'disabled_on_after',
        'disabled_on_before',
        'event_type',
        'lead_team',
        'name',
        'organiser',
        'organiser_name',
        'start_date_after',
        'start_date_before',
        'teams',
        'uk_region',
    )

    REMAP_FIELDS = {
        'address_country': 'address_country.id',
        'event_type': 'event_type.id',
        'lead_team': 'lead_team.id',
        'name': 'name_trigram',
        'organiser': 'organiser.id',
        'organiser_name': 'organiser.name_trigram',
        'teams': 'teams.id',
        'uk_region': 'uk_region.id',
    }


class SearchEventAPIView(SearchEventParams, SearchAPIView):
    """Filtered event search view."""

    permission_classes = SearchAPIView.permission_classes + (UserHasPermissions,)
    permission_required = 'event.read_event'


class SearchEventExportAPIView(SearchEventParams, SearchExportAPIView):
    """Filtered event search export view."""

    permission_classes = SearchAPIView.permission_classes + (UserHasPermissions,)
    permission_required = 'event.read_event'
