from datahub.company.models.contact import Contact
from datahub.core.query_utils import get_full_name_expression


def get_base_contact_queryset():
    Contact.objects.annotate(
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
