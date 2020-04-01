from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.settings import api_settings

from datahub.search.apps import get_global_search_apps_as_mapping
from datahub.search.query_builder import MAX_RESULTS
from datahub.search.utils import SearchOrdering, SortDirection


class SingleOrListField(serializers.ListField):
    """Field can be single instance or list."""

    def to_internal_value(self, data):
        """
        If data is str, call the child serialiser's run_validation() directly.

        This is to maintain an error format matching the input (if a list is provided, return an
        error list for each item, otherwise return a single error list).

        (We call self.child.run_validation() rather than self.child.to_internal_value(), because
        ListField performs child field validation in its to_internal_value().)
        """
        if isinstance(data, str):
            return [self.child.run_validation(data)]
        return super().to_internal_value(data)


class StringUUIDField(serializers.UUIDField):
    """
    String UUID field.

    We can't use UUID in ES queries, that's why we need to convert them back to string.
    """

    def to_internal_value(self, data):
        """
        Converts string to UUID and then back to string,
        to ensure that string is valid UUID.
        """
        uuid = super().to_internal_value(data)
        return str(uuid)


class IdNameSerializer(serializers.Serializer):
    """Serializer to return metadata constant with id and name."""

    id = StringUUIDField()
    name = serializers.CharField()


class _ESOrderingField(serializers.Field):
    """Serialiser field for specifying an ordering for a search."""

    default_error_messages = {
        'invalid_field': gettext_lazy('"{input}" is not a valid choice for the sort field.'),
        'invalid_direction': gettext_lazy('"{input}" is not a valid sort direction.'),
    }
    default_direction = SortDirection.asc

    def __init__(self, *args, **kwargs):
        """Initialise the field."""
        super().__init__(*args, **kwargs)
        self.choices = None

    def configure(self, choices, default):
        """Sets the choices and default ordering for the field."""
        self.choices = choices
        self.default = default

    def to_internal_value(self, data):
        """Converts an ordering string to an SearchOrdering."""
        field, _, direction = data.partition(':')

        if field not in self.choices:
            self.fail('invalid_field', input=field)

        if direction:
            try:
                direction = SortDirection(direction)
            except ValueError:
                self.fail('invalid_direction', input=direction)
        else:
            direction = self.default_direction

        return SearchOrdering(field, direction)

    def to_representation(self, value):
        """Converts an SearchOrdering to an ordering string."""
        return f'{value.field}:{value.direction}'


class BaseSearchQuerySerializer(serializers.Serializer):
    """Base serialiser for basic (global) and entity search."""

    SORT_BY_FIELDS = []

    DEFAULT_ORDERING = None

    offset = serializers.IntegerField(default=0, min_value=0, max_value=MAX_RESULTS - 1)
    limit = serializers.IntegerField(default=api_settings.PAGE_SIZE, min_value=1)
    sortby = _ESOrderingField(required=False)

    def __init__(self, *args, **kwrags):
        """Initialises the serialiser and configures the `sortby` field."""
        super().__init__(*args, **kwrags)
        self.fields['sortby'].configure(self.SORT_BY_FIELDS, self.DEFAULT_ORDERING)


class _ESModelChoiceField(serializers.Field):
    """Serialiser field for selecting an ES model by name."""

    default_error_messages = {
        'invalid_choice': gettext_lazy('"{input}" is not a valid choice.'),
    }

    def get_default(self):
        """Gets the default value for the field."""
        default = super().get_default()
        if isinstance(default, str):
            return self.to_internal_value(default)

        return default

    def to_internal_value(self, data):
        """Translates a model name to a model."""
        global_search_models = get_global_search_apps_as_mapping()
        if data not in global_search_models:
            self.fail('invalid_choice', input=data)
        return global_search_models[data].es_model

    def to_representation(self, value):
        """Translates a model to a model name."""
        return value.get_app_name()


class BasicSearchQuerySerializer(BaseSearchQuerySerializer):
    """Serialiser used to validate basic (global) search query parameters."""

    entity = _ESModelChoiceField(default='company')
    term = serializers.CharField(required=True, allow_blank=True)


class EntitySearchQuerySerializer(BaseSearchQuerySerializer):
    """Serialiser used to validate entity search POST bodies."""

    original_query = serializers.CharField(default='', allow_blank=True)


class AutocompleteSearchQuerySerializer(serializers.Serializer):
    """Serialiser used for the autocomplation search query parameters."""

    term = serializers.CharField(required=True, allow_blank=True)
    limit = serializers.IntegerField(default=10, min_value=1)
