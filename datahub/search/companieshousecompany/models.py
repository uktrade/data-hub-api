from django.conf import settings
from elasticsearch_dsl import Date, DocType, Keyword, Text

from datahub.search import dict_utils, dsl_utils
from datahub.search.models import MapDBModelToDict


class CompaniesHouseCompany(DocType, MapDBModelToDict):
    """Elasticsearch representation of CompaniesHouseCompany model."""

    id = Keyword()
    name = dsl_utils.SortableText(copy_to=['name_keyword', 'name_trigram'])
    name_keyword = dsl_utils.SortableCaseInsensitiveKeywordText()
    name_trigram = dsl_utils.TrigramText()
    registered_address_1 = Text()
    registered_address_2 = Text()
    registered_address_town = dsl_utils.SortableCaseInsensitiveKeywordText()
    registered_address_county = Text()
    registered_address_postcode = Text()
    registered_address_country = dsl_utils.id_name_mapping()
    company_number = dsl_utils.SortableCaseInsensitiveKeywordText()
    company_category = dsl_utils.SortableCaseInsensitiveKeywordText()
    company_status = dsl_utils.SortableCaseInsensitiveKeywordText()
    sic_code_1 = dsl_utils.SortableCaseInsensitiveKeywordText()
    sic_code_2 = dsl_utils.SortableCaseInsensitiveKeywordText()
    sic_code_3 = dsl_utils.SortableCaseInsensitiveKeywordText()
    sic_code_4 = dsl_utils.SortableCaseInsensitiveKeywordText()
    uri = dsl_utils.SortableCaseInsensitiveKeywordText()
    incorporation_date = Date()

    MAPPINGS = {
        'id': str,
        'registered_address_country': dict_utils.id_name_dict,
    }

    SEARCH_FIELDS = [
        'company_number',
    ]

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'companieshousecompany'
