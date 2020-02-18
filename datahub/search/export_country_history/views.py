# from elasticsearch_dsl.query import Bool, Match, MultiMatch, Q
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope

# from datahub.company.models import CompanyExportCountryHistory as DBCompanyExportCountryHistory
from datahub.oauth.scopes import Scope
from datahub.search.export_country_history import ExportCountryHistoryApp
from datahub.search.export_country_history.serializers import SearchExportCountryHistorySerializer
from datahub.search.interaction.models import Interaction
from datahub.search.permissions import SearchPermissions
from datahub.search.views import register_v4_view, SearchAPIView


@register_v4_view()
class ExportCountryHistoryView(SearchAPIView):
    """Export country history search view."""

    required_scopes = (Scope.internal_front_end,)
    search_app = ExportCountryHistoryApp

    permission_classes = (IsAuthenticatedOrTokenHasScope, SearchPermissions)
    FILTER_FIELDS = [
        'country',
        'company',
    ]

    REMAP_FIELDS = {
        'company': 'company.id',
        'country': 'country.id',
    }

    serializer_class = SearchExportCountryHistorySerializer

    def get_entities(self):
        """
        Overriding to provide multiple entities
        """
        return [self.search_app.es_model, Interaction]

    def get_filter_data(self, validated_data):
        """
        Overriding to add extra filters
        """
        filter_data = {
            **super().get_filter_data(validated_data),
            # 'were_countries_discussed': True,
        }
        return filter_data

    def get_base_query(self, request, validated_data):
        """
        Overriding to extra query items to exlcude:
        interactions without export countries
        and UPDATE history items
        """
        base_query = super().get_base_query(request, validated_data)
        # 1
        # base_query = base_query.filter('match', **{'were_countries_discussed': True}) \
        #     .exclude('match', **{
        #         'history_type': DBCompanyExportCountryHistory.HistoryType.UPDATE
        #     })
        # 2
        # field_query = {
        #     'query': True,
        #     'operator': 'and',
        # }
        # should_filter = [Match(**{'were_countries_discussed': field_query})]
        # 3
        # base_query.query(Bool(should=should_filter, minimum_should_match=1))
        # 4
        # base_query = base_query.filter('term', **{'were_countries_discussed': True})
        # 5
        # sub_query = Q(
        #   Q('match', **{'were_countries_discussed': True}) & \
        #   Q('match', **{'_type': 'export-country-history'})
        # ) | Q('match', **{'_type': 'interaction'})
        # base_query = base_query.query(sub_query)
        # print(base_query.to_dict())
        return base_query
