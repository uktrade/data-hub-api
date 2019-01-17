from elasticsearch_dsl import Date, Keyword, Text

from datahub.search import dict_utils, fields
from datahub.search.models import BaseESModel


DOC_TYPE = 'companieshousecompany'


class CompaniesHouseCompany(BaseESModel):
    """Elasticsearch representation of CompaniesHouseCompany model."""

    id = Keyword()
    company_category = fields.NormalizedKeyword()
    company_number = fields.NormalizedKeyword()
    company_status = fields.NormalizedKeyword()
    incorporation_date = Date()
    name = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    registered_address_1 = Text()
    registered_address_2 = Text()
    registered_address_town = fields.NormalizedKeyword()
    registered_address_county = Text()
    registered_address_postcode = Text(copy_to='registered_address_postcode_trigram')
    registered_address_postcode_trigram = fields.TrigramText()
    registered_address_country = fields.id_name_field()
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
        'name.trigram',
        'company_number',
        'registered_address_postcode_trigram',
    )

    class Meta:
        """Default document meta data."""

        doc_type = DOC_TYPE

    class Index:
        doc_type = DOC_TYPE
