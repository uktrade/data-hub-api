from elasticsearch_dsl import Date, Keyword

from datahub.search import dict_utils, fields
from datahub.search.models import BaseESModel, DEFAULT_MAPPING_TYPE


class ExportCountryHistory(BaseESModel):
    """Elasticsearch representation of CompanyExportCountryHistory model."""

    id = Keyword()
    history_date = Date(index=False)
    history_user = fields.id_unindexed_name_field()
    history_type = Keyword(index=True)
    country = fields.id_unindexed_name_field()

    company = fields.id_unindexed_name_field()
    status = Keyword(index=False)
    # Adding `date` field, mapping to `history_date` for sorting across entities
    # export_country_history and interaction.
    date = Date()

    MAPPINGS = {
        'history_user': dict_utils.id_name_dict,
        'country': dict_utils.id_name_dict,
        'company': dict_utils.id_name_dict,
    }

    COMPUTED_MAPPINGS = {
        'id': lambda obj: obj.history_id,  # Id required for indexing
        'date': lambda obj: obj.history_date,
    }

    class Meta:
        """Default document meta data."""

        doc_type = DEFAULT_MAPPING_TYPE

    class Index:
        doc_type = DEFAULT_MAPPING_TYPE
