from elasticsearch_dsl import Date, Keyword, Text

from datahub.search import dict_utils, fields
from datahub.search.models import BaseESModel

DOC_TYPE = 'export-country-history'


class ExportCountryHistory(BaseESModel):
    """Elasticsearch representation of CompanyExportCountryHistory model."""

    id = Keyword()
    history_id = Keyword()
    history_date = Date()
    history_user = fields.contact_or_adviser_field()
    history_type = Text()
    country = fields.id_name_field()

    company = fields.id_name_partial_field()
    status = Text()

    MAPPINGS = {
        'history_user': dict_utils.id_name_dict,
        'country': dict_utils.id_name_dict,
        'company': dict_utils.id_name_dict,
    }

    SEARCH_FIELDS = (
        'country',
        'company',
        'history_date',
        'history_user',
    )

    class Meta:
        """Default document meta data."""

        doc_type = DOC_TYPE

    class Index:
        doc_type = DOC_TYPE
