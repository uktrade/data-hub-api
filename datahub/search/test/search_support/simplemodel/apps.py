from datahub.search.apps import SearchApp
from datahub.search.test.search_support.models import SimpleModel as DBSimpleModel
from datahub.search.test.search_support.simplemodel.models import ESSimpleModel


class SimpleModelSearchApp(SearchApp):
    """SearchApp for SimpleModel."""

    name = 'simplemodel'
    es_model = ESSimpleModel
    queryset = DBSimpleModel.objects
    view_permissions = ['search_support.view_simplemodel']
    export_permission = 'search_support.view_simplemodel'
