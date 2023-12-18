import logging

import reversion

from datahub.company.merge import (
    _default_object_updater,
    is_model_a_valid_merge_source,
    is_model_a_valid_merge_target,
    MergeConfiguration,
    MergeNotAllowedError,
    update_objects,
)
from datahub.company.models import (
    Company,
    CompanyExportCountry,
    CompanyExportCountryHistory,
    Contact,
)
from datahub.company_referral.models import CompanyReferral
from datahub.dnb_api.utils import _get_rollback_version
from datahub.interaction.models import Interaction
from datahub.investment.project.models import InvestmentProject
from datahub.omis.order.models import Order
from datahub.user.company_list.models import CompanyListItem, PipelineItem

logger = logging.getLogger(__name__)

# Merging is not allowed if the source company has any relations that aren't in
# this list. This is to avoid references to the source company being inadvertently
# left behind.
ALLOWED_RELATIONS_FOR_MERGING = {
    # These relations are moved to the target company on merge
    Company._meta.get_field('company_list_items').remote_field,
    Company._meta.get_field('pipeline_list_items').remote_field,
    Company._meta.get_field('wins').remote_field,
    CompanyReferral.company.field,
    Contact.company.field,
    Interaction.company.field,
    Interaction.companies.field,
    InvestmentProject.investor_company.field,
    InvestmentProject.intermediate_company.field,
    InvestmentProject.uk_company.field,
    Order.company.field,

    # Merging is allowed if the source company has export countries, but note that
    # they aren't moved to the target company (these can be manually moved in
    # the front end if required)
    CompanyExportCountry.company.field,
    CompanyExportCountryHistory.company.field,
}


INVESTMENT_PROJECT_COMPANY_FIELDS = (
    'investor_company',
    'intermediate_company',
    'uk_company',
)

FIELD_TO_DESCRIPTION_MAPPING = {
    'companies': ' as one of participating companies',
    'investor_company': ' as investor company',
    'intermediate_company': ' as intermediate company',
    'uk_company': ' as UK company',
}


def _company_list_item_updater(list_item, field, target_company, source_company):
    # If there is already a list item for the target company, delete this list item instead
    # as duplicates are not allowed
    if CompanyListItem.objects.filter(list_id=list_item.list_id, company=target_company).exists():
        list_item.delete()
    else:
        _default_object_updater(list_item, field, target_company, source_company)


def _pipeline_item_updater(pipeline_item, field, target_company, source_company):
    # If there is already a pipeline item for the adviser for the target company
    # delete this item instead as the same company can't be added for the same adviser again
    if PipelineItem.objects.filter(adviser=pipeline_item.adviser, company=target_company).exists():
        pipeline_item.delete()
    else:
        _default_object_updater(pipeline_item, field, target_company, source_company)


MERGE_CONFIGURATION = [
    MergeConfiguration(Interaction, ('company', 'companies'), Company),
    MergeConfiguration(CompanyReferral, ('company',), Company),
    MergeConfiguration(Contact, ('company',), Company),
    MergeConfiguration(InvestmentProject, INVESTMENT_PROJECT_COMPANY_FIELDS, Company),
    MergeConfiguration(Order, ('company',), Company),
    MergeConfiguration(CompanyListItem, ('company',), Company, _company_list_item_updater),
    MergeConfiguration(PipelineItem, ('company',), Company, _pipeline_item_updater),
]


def merge_companies(source_company: Company, target_company: Company, user):
    """
    Merges the source company into the target company.
    MergeNotAllowedError will be raised if the merge is not allowed.
    """
    is_source_valid, invalid_obj = is_model_a_valid_merge_source(
        source_company,
        ALLOWED_RELATIONS_FOR_MERGING,
        Company,
    )
    is_target_valid = is_model_a_valid_merge_target(target_company)

    if not (is_source_valid and is_target_valid):
        logger.error(
            f"""MergeNotAllowedError {source_company.id}
            for company {target_company.id}.
            Invalid bojects: {invalid_obj}""",
        )
        raise MergeNotAllowedError()

    with reversion.create_revision():
        reversion.set_comment('Company merged')
        try:
            results = {
                configuration.model: update_objects(configuration, source_company, target_company)
                for configuration in MERGE_CONFIGURATION
            }

        except Exception as e:
            logger.exception(f'An error occurred while merging companies: {e}')
            raise

        source_company.mark_as_transferred(
            target_company,
            Company.TransferReason.DUPLICATE,
            user,
        )
        logger.info(f'Merge completed {source_company.id} for company {target_company.id}.')
        return results


def rollback_merge_companies(former_source_company: Company):
    """
    Rolls back a company merge of what was the "source_company" passed to merge_companies
    """
    rollback_version = _get_rollback_version(former_source_company, 'Company merged')
    rollback_version.revision.revert()
