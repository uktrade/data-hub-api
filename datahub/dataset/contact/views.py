from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from datahub.company import consent
from datahub.company.constants import GET_CONSENT_FROM_CONSENT_SERVICE
from datahub.company.models.contact import Contact
from datahub.core.query_utils import get_full_name_expression
from datahub.dataset.core.views import BaseDatasetView
from datahub.feature_flag.utils import is_feature_flag_active


class ContactsDatasetView(BaseDatasetView):
    """
    An APIView that provides 'get' action which queries and returns desired fields for
    Contacts Dataset to be consumed by Data-flow periodically. Data-flow uses response result
    to insert data into Dataworkspace through its defined API endpoints. The goal is presenting
    various reports to the users out of flattened table and let analyst to work on denormalized
    table to get more meaningful insight.
    """

    def _is_valid_email(self, value):
        """Validate if emails are valid and return a boolean flag."""
        try:
            validate_email(value)
            return True
        except ValidationError:
            return False

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
            'created_by_id',
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

    def _enrich_data(self, data):
        """
        Get the marketing consent from the consent service.

        Strip invalid emails from the data, old data may be
        empty or invalid due to validation implemented at a later date.
        """
        if is_feature_flag_active(GET_CONSENT_FROM_CONSENT_SERVICE):
            emails = [item['email'] for item in data if self._is_valid_email(item['email'])]
            consent_lookups = consent.get_many(emails)
            for item in data:
                item['accepts_dit_email_marketing'] = consent_lookups.get(item['email'], False)
        return data
