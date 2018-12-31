from elasticsearch_dsl import Date, Keyword, Object, Text

from datahub.search import dict_utils, fields
from datahub.search.inner_docs import UnindexedInnerIDName
from datahub.search.models import BaseESModel


DOC_TYPE = 'companieshousecompany'


class CompaniesHouseCompany(BaseESModel):
    """Elasticsearch representation of CompaniesHouseCompany model."""

    id = Keyword()
    company_category = Keyword(index=False)
    company_number = fields.NormalizedKeyword()
    company_status = Keyword(index=False)
    incorporation_date = Date(index=False)
    name = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    registered_address_1 = Text(index=False)
    registered_address_2 = Text(index=False)
    registered_address_town = Text(index=False)
    registered_address_county = Text(index=False)
    registered_address_postcode = Text(
        fields={
            'trigram': fields.TrigramText(),
        },
    )
    registered_address_country = Object(UnindexedInnerIDName)
    sic_code_1 = Text(index=False)
    sic_code_2 = Text(index=False)
    sic_code_3 = Text(index=False)
    sic_code_4 = Text(index=False)

    MAPPINGS = {
        'id': str,
        'registered_address_country': dict_utils.id_name_dict,
    }

    SEARCH_FIELDS = (
        # to match names like A & B
        'name',
        'name.trigram',
        'company_number',
        'registered_address_postcode.trigram',
        # Fields from previous version of mapping. TODO: Remove these once all environments have
        # been updated to the new mapping
        'name_trigram',
        'registered_address_postcode_trigram',
    )

    class Meta:
        """Default document meta data."""

        doc_type = DOC_TYPE

    class Index:
        doc_type = DOC_TYPE
