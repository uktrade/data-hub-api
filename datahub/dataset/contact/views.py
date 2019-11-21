from datahub.company.models.contact import Contact
from datahub.core.query_utils import get_full_name_expression
from datahub.dataset.core.views import BaseDatasetView


class ContactsDatasetView(BaseDatasetView):
    """
    An APIView that provides 'get' action which queries and returns desired fields for
    Contacts Dataset to be consumed by Data-flow periodically. Data-flow uses response result
    to insert data into Dataworkspace through its defined API endpoints. The goal is presenting
    various reports to the users out of flattened table and let analyst to work on denormalized
    table to get more meaningful insight.
    """

    def get_dataset(self):
        """Returns list of Contacts Dataset records"""
        return Contact.objects.annotate(
            name=get_full_name_expression(),
        ).values(
            'accepts_dit_email_marketing',
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
            'created_on',
            'email',
            'email_alternative',
            'id',
            'job_title',
            'modified_on',
            'name',
            'notes',
            'primary',
            'telephone_alternative',
            'telephone_number',
        )
