from django_filters.rest_framework import CharFilter, FilterSet

from datahub.core.autocomplete import AutocompleteFilter
from datahub.metadata.models import Service, Team


class ServiceFilterSet(FilterSet):
    """Filters for the service view."""

    contexts__has_any = CharFilter(field_name='contexts', method='filter_contexts__has_any')

    def filter_contexts__has_any(self, queryset, field_name, value):
        """Filters by checking if contexts contains any of a number of values.

        Multiple values are separated by a comma.
        """
        filter_args = {
            f'{field_name}__overlap': value.split(','),
        }
        return queryset.filter(**filter_args)

    class Meta:
        model = Service
        fields = ()


class TeamFilterSet(FilterSet):
    """Team filter."""

    autocomplete = AutocompleteFilter(search_fields=('name',))

    class Meta:
        model = Team
        fields = ('id',)
