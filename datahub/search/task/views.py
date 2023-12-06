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
    fields_to_exclude = ()

    FILTER_FIELDS = (
        'archived',
        'id',
        'title',
        'due_date',
        'created_by',
        'not_created_by',
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

    COMPOSITE_FILTERS = {}


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
        base_query = super().get_base_query(request, validated_data)

        raw_query = base_query.to_dict()
        filters = self.deep_get(raw_query, 'query|bool|filter')
        if not filters:
            return base_query
        # from pprint import pprint

        if request.data.get('not_created_by'):
            filters = [
                {
                    'bool': {
                        'must_not': [
                            {
                                'bool': {
                                    'minimum_should_match': 1,
                                    'should': [
                                        {
                                            'match': {
                                                'created_by.id': {
                                                    'operator': 'and',
                                                    'query': request.data['not_created_by'],
                                                },
                                            },
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                },
            ]
            raw_query['query']['bool']['filter'] = filters
            base_query.update_from_dict(raw_query)

        # filter_index = None
        # for index, filter in enumerate(filters):
        #     if filter.get('bool'):
        #         filter_index = index
        #         break

        # if filter_index is None:
        #     return base_query

        # must_filters = filters[filter_index]['bool']['must']
        # for index, filter in enumerate(must_filters):
        #     # By default the logic to generate an opensearch query inside get_base_query uses an
        #     # and for each column passed to it. In this use case, when we detect a query for the
        #     # ghq headquarter id we add an addiitonal should entry into the should array
        #     should_queries = self.deep_get(filter, 'bool|should')

        #     if should_queries:
        #         for should_query in should_queries:
        #             if (
        #                 self.deep_get(should_query, 'match|headquarter_type.id|query')
        #                 == HeadquarterType.ghq.value.id
        #             ):
        #                 should_queries.append(
        #                     {
        #                         'match': {
        #                             'is_global_ultimate': {
        #                                 'query': True,
        #                             },
        #                         },
        #                     },
        #                 )
        #                 break
        #         base_query.filter('terms', tags=['search', 'python'])
        #         raw_query['query']['bool']['filter'][filter_index]['bool']['must'][index]['bool'][
        #             'should'
        #         ] = should_queries

        # raw_query['query']['bool']['filter'] = filters
        # pprint("post raw_query:")
        # pprint(raw_query)
        # base_query.update_from_dict(raw_query)

        # base_query.filter('terms', tags=['search', 'python'])
        return base_query
