from django.conf import settings
from elasticsearch_dsl import Date, DocType, Keyword, Text

from datahub.search import dict_utils, dsl_utils
from datahub.search.models import MapDBModelToDict


class CompaniesHouseCompany(DocType, MapDBModelToDict):
    """Elasticsearch representation of CompaniesHouseCompany model.

    Following fields are copied to "global_search":
    - company_number
    - name
    """

    id = Keyword()
    global_search = dsl_utils.TrigramText()
    name = dsl_utils.SortableText(
        copy_to=[
            'name_keyword', 'name_trigram', 'global_search'
        ]
    )
    name_keyword = dsl_utils.SortableCaseInsensitiveKeywordText()
    name_trigram = dsl_utils.SortableTrigramText()
    registered_address_1 = Text()
    registered_address_2 = Text()
    registered_address_town = dsl_utils.SortableCaseInsensitiveKeywordText()
    registered_address_county = Text()
    registered_address_postcode = Text()
    registered_address_country = dsl_utils.id_name_mapping()
    company_number = dsl_utils.SortableCaseInsensitiveKeywordText(
        copy_to=['global_search']
    )
    company_category = dsl_utils.SortableCaseInsensitiveKeywordText()
    company_status = dsl_utils.SortableCaseInsensitiveKeywordText()
    sic_code_1 = Text()
    sic_code_2 = Text()
    sic_code_3 = Text()
    sic_code_4 = Text()
    uri = Text()
    incorporation_date = Date()

    MAPPINGS = {
        'id': str,
        'registered_address_country': dict_utils.id_name_dict,
    }

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'companieshousecompany'
