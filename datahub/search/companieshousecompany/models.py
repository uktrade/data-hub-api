from elasticsearch_dsl import Date, Keyword, Text

from datahub.search import dict_utils, dsl_utils
from datahub.search.models import BaseESModel


class CompaniesHouseCompany(BaseESModel):
    """Elasticsearch representation of CompaniesHouseCompany model."""

    id = Keyword()
    company_category = dsl_utils.SortableCaseInsensitiveKeywordText()
    company_number = dsl_utils.SortableCaseInsensitiveKeywordText()
    company_status = dsl_utils.SortableCaseInsensitiveKeywordText()
    incorporation_date = Date()
    name = dsl_utils.SortableText(
        copy_to=[
            'name_keyword', 'name_trigram'
        ]
    )
    name_keyword = dsl_utils.SortableCaseInsensitiveKeywordText()
    name_trigram = dsl_utils.TrigramText()
    registered_address_1 = Text()
    registered_address_2 = Text()
    registered_address_town = dsl_utils.SortableCaseInsensitiveKeywordText()
    registered_address_county = Text()
    registered_address_postcode = Text(copy_to='registered_address_postcode_trigram')
    registered_address_postcode_trigram = dsl_utils.TrigramText()
    registered_address_country = dsl_utils.id_name_mapping()
    sic_code_1 = Text()
    sic_code_2 = Text()
    sic_code_3 = Text()
    sic_code_4 = Text()
    uri = Text()

    MAPPINGS = {
        'id': str,
        'registered_address_country': dict_utils.id_name_dict,
    }

    SEARCH_FIELDS = (
        # to match names like A & B
        'name',
        'name_trigram',
        'company_number',
        'registered_address_postcode_trigram',
    )

    class Meta:
        """Default document meta data."""

        doc_type = 'companieshousecompany'
