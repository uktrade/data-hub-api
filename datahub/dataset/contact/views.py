from datahub.company.models.contact import Contact
from datahub.core.query_utils import get_full_name_expression
from datahub.dataset.core.views import BaseFilterDatasetView
from datahub.dataset.utils import filter_data_by_modified_date


class ContactsDatasetView(BaseFilterDatasetView):
    """An APIView that provides 'get' action which queries and returns desired fields for
    Contacts Dataset to be consumed by Data-flow periodically. Data-flow uses response result
    to insert data into Dataworkspace through its defined API endpoints. The goal is presenting
    various reports to the users out of flattened table and let analyst to work on denormalized
    table to get more meaningful insight.
    """

    def get_dataset(self, request):
        """Returns list of Contacts Dataset records."""
        queryset = Contact.objects.annotate(
            name=get_full_name_expression(),
        ).values(
            'address_1',
            'address_2',
            'address_country__name',
            'address_county',
            'address_postcode',
            'address_same_as_company',
            'address_town',
            'archived',
            'archived_on',
            'company_id',
            'created_by_id',
            'created_on',
            'email',
            'first_name',
            'id',
            'job_title',
            'last_name',
            'modified_on',
            'name',
            'notes',
            'primary',
            'full_telephone_number',
            'valid_email',
        )
        updated_since = request.GET.get('updated_since')

        filtered_queryset = filter_data_by_modified_date(updated_since, queryset)

        return filtered_queryset
