from functools import reduce

from datahub.search.task import TaskSearchApp
from datahub.search.task.serializers import (
    SearchTaskQuerySerializer,
)
from datahub.search.views import (
    register_v4_view,
    SearchAPIView,
)


class SearchTaskAPIViewMixin:
    """Defines common settings."""

    search_app = TaskSearchApp
    serializer_class = SearchTaskQuerySerializer
    es_sort_by_remappings = {}
    fields_to_exclude = ('not_created_by', 'not_advisers')

    FILTER_FIELDS = (
        'archived',
        'id',
        'title',
        'due_date',
        'created_by',
        'advisers',
        'company',
        'investment_project',
    )

    REMAP_FIELDS = {
        'advisers': 'advisers.id',
        'created_by': 'created_by.id',
        'company': 'company.id',
        'investment_project': 'investment_project.id',
    }


@register_v4_view()
class SearchTaskAPIView(SearchTaskAPIViewMixin, SearchAPIView):
    """Filtered company search view."""

    def deep_get(self, dictionary, keys, default=None):
        """
        Perform a deep search on a dictionary to find the item at the location provided in the keys
        """
        return reduce(
            lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
            keys.split('|'),
            dictionary,
        )

    def get_base_query(self, request, validated_data):
        """
        Check for filters that filter for not_* parameters and extend the open search base query
        with the must_not filters.
        """
        must_not = []
        base_query = super().get_base_query(request, validated_data)

        if request.data.get('not_created_by'):
            must_not.append(
                {
                    'match': {
                        'created_by.id': {
                            'operator': 'and',
                            'query': request.data['not_created_by'],
                        },
                    },
                },
            )

        if request.data.get('not_advisers'):
            must_not.append(
                {
                    'bool': {
                        'minimum_should_match': 1,
                        'should': [
                            {
                                'match': {'advisers.id': {'operator': 'and', 'query': adviser}},
                            }
                            for adviser in request.data['not_advisers']
                        ],
                    },
                },
            )

        if len(must_not) > 0:
            raw_query = base_query.to_dict()
            filters = self.deep_get(raw_query, 'query|bool|filter')
            if not filters:
                return base_query

            filter_index = None
            for index, filter in enumerate(filters):
                if filter.get('bool') or filter.get('bool') == {}:
                    filter_index = index
                    break

            if filter_index is None:
                return base_query

            filters[filter_index]['bool']['must_not'] = must_not
            raw_query['query']['bool']['filter'] = filters

            base_query.update_from_dict(raw_query)
        return base_query
