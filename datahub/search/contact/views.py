from rest_framework.views import APIView

from .models import Contact
from ..views import SearchWithFiltersAPIMixin


class SearchContactAPIView(SearchWithFiltersAPIMixin, APIView):
    """Filtered contact search view."""

    entity = Contact

    SORT_BY_FIELDS = (
        'address_country.name',
        'address_county',
        'address_same_as_company',
        'address_town',
        'adviser.name',
        'archived',
        'archived_by.name',
        'company.name',
        'contactable_by_dit',
        'contactable_by_dit_partners',
        'contactable_by_email',
        'contactable_by_phone',
        'created_on',
        'email',
        'first_name',
        'id',
        'job_title',
        'last_name',
        'modified_on',
        'name',
        'primary',
        'telephone_countrycode',
        'telephone_number',
        'title.name'
    )

    FILTER_FIELDS = (
        'company_name',
        'company_sector',
        'company_uk_region',
        'address_country',
    )

    REMAP_FIELDS = {
        'company_name': 'company.name_trigram',
        'company_sector': 'company_sector.id',
        'company_uk_region': 'company_uk_region.id',
        'address_country': 'address_country.id',
    }
