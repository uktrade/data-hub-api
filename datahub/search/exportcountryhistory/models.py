from elasticsearch_dsl import Date, Keyword

from datahub.search import dict_utils, fields
from datahub.search.models import BaseESModel

DOC_TYPE = 'export-country-history'


class ExportCountryHistory(BaseESModel):
    """Elasticsearch representation of CompanyExportCountryHistory model."""

    id = Keyword()
    history_date = Date(index=False)
    history_user = fields.id_unindexed_name_field()
    history_type = Keyword()
    country = fields.id_unindexed_name_field()

    company = fields.id_unindexed_name_field()
    status = Keyword(index=False)

    MAPPINGS = {
        'history_user': dict_utils.id_name_dict,
        'country': dict_utils.id_name_dict,
        'company': dict_utils.id_name_dict,
    }

    COMPUTED_MAPPINGS = {
        'id': lambda obj: obj.history_id,
    }

    class Meta:
        """Default document meta data."""

        doc_type = DOC_TYPE

    class Index:
        doc_type = DOC_TYPE
