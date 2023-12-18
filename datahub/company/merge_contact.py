import logging

import reversion

from datahub.company.merge import (
    is_model_a_valid_merge_source,
    is_model_a_valid_merge_target,
    MergeConfiguration,
    MergeNotAllowedError,
    update_objects,
)
from datahub.company.models import CompanyExport, Contact
from datahub.company_referral.models import CompanyReferral
from datahub.interaction.models import Interaction
from datahub.investment.project.models import InvestmentProject
from datahub.omis.order.models import Order, Quote
from datahub.user.company_list.models import PipelineItem

logger = logging.getLogger(__name__)

ALLOWED_RELATIONS_FOR_MERGING = {
    # These relations are moved to the target company on merge
    Contact._meta.get_field('pipeline_items_m2m').remote_field,
    CompanyReferral.contact.field,
    Interaction.contacts.field,
    InvestmentProject.client_contacts.field,
    Order.contact.field,
    CompanyExport.contacts.field,

    # Merging is allowed if the source contact has quotes, but note that
    # they aren't moved to the target contact
    Quote.accepted_by.field,
}


MERGE_CONFIGURATION = [
    MergeConfiguration(Interaction, ('contacts',), Contact),
    MergeConfiguration(CompanyReferral, ('contact',), Contact),
    MergeConfiguration(InvestmentProject, ('client_contacts',), Contact),
    MergeConfiguration(Order, ('contact',), Contact),
    MergeConfiguration(CompanyExport, ('contacts',), Contact),
    MergeConfiguration(PipelineItem, ('contacts',), Contact),
]


def merge_contacts(source_contact: Contact, target_contact: Contact, user):
    """
    Merges the source contact into the target contact.

    MergeNotAllowedError will be raised if the merge is not allowed.
    """
    is_source_valid, invalid_obj = is_model_a_valid_merge_source(
        source_contact, ALLOWED_RELATIONS_FOR_MERGING, Contact)
    is_target_valid = is_model_a_valid_merge_target(target_contact)

    if not (is_source_valid and is_target_valid):
        logger.error(
            f"""MergeNotAllowedError {source_contact.id}
            for contact {target_contact.id}.
            Invalid bojects: {invalid_obj}""",
        )
        raise MergeNotAllowedError()

    with reversion.create_revision():
        reversion.set_comment('contact merged')
        try:
            results = {
                configuration.model: update_objects(configuration, source_contact, target_contact)
                for configuration in MERGE_CONFIGURATION
            }
        except Exception as e:
            logger.exception(f'An error occurred while merging companies: {e}')
            raise

        target_contact.merge_contact_fields(source_contact)
        source_contact.mark_as_transferred(
            target_contact,
            Contact.TransferReason.DUPLICATE,
            user,
        )
        logger.info(f'Merge completed {source_contact.id} for contact {target_contact.id}.')
        return results
