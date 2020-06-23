from datahub.company.models import Company
from datahub.dataset.core.views import BaseDatasetView
from datahub.metadata.query_utils import get_sector_name_subquery


class CompaniesDatasetView(BaseDatasetView):
    """
    A GET API view to return the data for all companies as required
    for syncing by Data-flow periodically.
    Data-flow uses the resulting response to insert data into Data workspace which can
    then be queried to create custom reports for users.
    """

    def get_dataset(self):
        """Returns list of Company records"""
        return Company.objects.annotate(
            sector_name=get_sector_name_subquery('sector'),
        ).values(
            'address_1',
            'address_2',
            'address_county',
            'address_country__name',
            'address_postcode',
            'address_town',
            'archived',
            'archived_on',
            'archived_reason',
            'business_type__name',
            'company_number',
            'created_by_id',
            'created_on',
            'description',
            'duns_number',
            'export_experience_category__name',
            'global_headquarters_id',
            'global_ultimate_duns_number',
            'headquarter_type__name',
            'id',
            'is_number_of_employees_estimated',
            'is_turnover_estimated',
            'modified_on',
            'name',
            'number_of_employees',
            'one_list_account_owner_id',
            'one_list_tier__name',
            'reference_code',
            'registered_address_1',
            'registered_address_2',
            'registered_address_country__name',
            'registered_address_county',
            'registered_address_postcode',
            'registered_address_town',
            'sector_name',
            'trading_names',
            'turnover',
            'uk_region__name',
            'vat_number',
            'website',
        )
