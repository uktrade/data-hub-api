from rest_framework.exceptions import ValidationError

from datahub.core.validate_utils import DataCombiner
from datahub.interaction.models import Interaction


class ContactsBelongToCompanyValidator:
    """Validates that an interaction's contacts belong to the interaction's company."""

    def __init__(self):
        """Initialises the validator."""
        self.instance = None

    def set_context(self, serializer):
        """Saves a reference to the model object."""
        self.instance = serializer.instance

    def __call__(self, data):
        """Performs validation."""
        company_has_changed = not self.instance or (
            'company' in data and data['company'] != self.instance.company
        )

        contacts_have_changed = not self.instance or (
            'contacts' in data and set(data['contacts']) != set(self.instance.contacts.all())
        )

        if not (company_has_changed or contacts_have_changed):
            return

        combiner = DataCombiner(self.instance, data)
        company = combiner.get_value('company')
        contacts = combiner.get_value_to_many('contacts')

        if any(contact.company != company for contact in contacts):
            raise ValidationError(
                'The interaction contacts must belong to the specified company.',
                code='inconsistent_contacts_and_company',
            )


class StatusChangeValidator:
    """
    Validates that an interaction's status cannot change from complete back to
    draft.  An interaction with status='complete' means that the interaction
    occurred successfully and any extra details for it have been logged.
    """

    def __init__(self):
        """
        Initialises the validator.
        """
        self.instance = None

    def set_context(self, serializer):
        """
        Saves a reference to the model object.
        """
        self.instance = serializer.instance

    def __call__(self, data):
        """
        Performs validation.
        """
        if not self.instance:
            return
        existing_interaction_complete = self.instance.status == Interaction.STATUSES.complete
        combiner = DataCombiner(self.instance, data)
        new_status = combiner.get_value('status')
        update_changes_status = new_status != self.instance.status
        if existing_interaction_complete and update_changes_status:
            raise ValidationError(
                'The status of a complete interaction cannot change.',
                code='complete_interaction_status_cannot_change',
            )
