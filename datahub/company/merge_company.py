import logging

import reversion

from datahub.company.merge import (
    get_planned_changes,
    is_model_a_valid_merge_source,
    is_model_a_valid_merge_target,
    MergeConfiguration,
    MergeNotAllowedError,
    update_objects,
)
from datahub.company.merge_utils.merge_relations import (
    company_list_item_updater,
    large_capital_opportunity_updater,
    one_list_core_team_member_updater,
    pipeline_item_updater,
)
from datahub.company.models import (
    Company,
    CompanyExport,
    CompanyExportCountry,
    CompanyExportCountryHistory,
    Contact,
    Objective,
    OneListCoreTeamMember,
)
from datahub.company_activity.models import CompanyActivity, GreatExportEnquiry
from datahub.company_referral.models import CompanyReferral
from datahub.dnb_api.utils import _get_rollback_version
from datahub.export_win.models import LegacyExportWinsToDataHubCompany
from datahub.interaction.models import Interaction
from datahub.investment.investor_profile.models import LargeCapitalInvestorProfile
from datahub.investment.opportunity.models import LargeCapitalOpportunity
from datahub.investment.project.models import InvestmentProject
from datahub.investment_lead.models import EYBLead
from datahub.omis.order.models import Order
from datahub.reminder.models import (
    NewExportInteractionReminder,
    NoRecentExportInteractionReminder,
)
from datahub.task.models import Task
from datahub.user.company_list.models import CompanyListItem, PipelineItem

logger = logging.getLogger(__name__)

# Merging is not allowed if the source company has any relations that aren't in
# this list. This is to avoid references to the source company being inadvertently
# left behind.
# EXCLUDE RELATIONS: To Exclude relations, add them here, don't add them to MERGE_CONFIGURATION.
ALLOWED_RELATIONS_FOR_MERGING = {
    # These relations are moved to the target company on merge
    Company._meta.get_field('company_list_items').remote_field,
    Company._meta.get_field('pipeline_list_items').remote_field,
    Company._meta.get_field('wins').remote_field,
    CompanyActivity.company.field,
    CompanyExport.company.field,
    CompanyReferral.company.field,
    Contact.company.field,
    EYBLead.company.field,
    GreatExportEnquiry.company.field,
    Interaction.company.field,
    Interaction.companies.field,
    InvestmentProject.investor_company.field,
    InvestmentProject.intermediate_company.field,
    InvestmentProject.uk_company.field,
    LargeCapitalInvestorProfile.investor_company.field,
    LargeCapitalOpportunity.promoters.field,
    LegacyExportWinsToDataHubCompany.company.field,
    NewExportInteractionReminder.company.field,
    NoRecentExportInteractionReminder.company.field,
    Objective.company.field,
    OneListCoreTeamMember.company.field,
    Order.company.field,
    Task.company.field,

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


# Models related to a company for merging companies and how to merge them.
# If its not a simple relation (like OneToMany) then you can specify a function for how each item
# is merged.
# Relations NOT added here but included in ALLOWED_RELATIONS_FOR_MERGING will NOT be merged.
MERGE_CONFIGURATION = [
    MergeConfiguration(Interaction, ('company', 'companies'), Company),
    MergeConfiguration(CompanyReferral, ('company',), Company),
    MergeConfiguration(CompanyActivity, ('company',), Company),
    MergeConfiguration(CompanyExport, ('company',), Company),
    MergeConfiguration(Contact, ('company',), Company),
    MergeConfiguration(EYBLead, ('company',), Company),
    MergeConfiguration(GreatExportEnquiry, ('company',), Company),
    MergeConfiguration(InvestmentProject, INVESTMENT_PROJECT_COMPANY_FIELDS, Company),
    MergeConfiguration(LargeCapitalInvestorProfile, ('investor_company',), Company),
    MergeConfiguration(
        LargeCapitalOpportunity, ('promoters',), Company, large_capital_opportunity_updater,
    ),
    MergeConfiguration(LegacyExportWinsToDataHubCompany, ('company',), Company),
    MergeConfiguration(Order, ('company',), Company),
    MergeConfiguration(NewExportInteractionReminder, ('company',), Company),
    MergeConfiguration(NoRecentExportInteractionReminder, ('company',), Company),
    MergeConfiguration(Task, ('company',), Company),
    MergeConfiguration(CompanyListItem, ('company',), Company, company_list_item_updater),
    MergeConfiguration(PipelineItem, ('company',), Company, pipeline_item_updater),
    MergeConfiguration(Objective, ('company',), Company),
    MergeConfiguration(
        OneListCoreTeamMember, ('company',), Company, one_list_core_team_member_updater,
    ),
]


def merge_companies(source_company: Company, target_company: Company, user):
    """
    Merges the source company into the target company.
    MergeNotAllowedError will be raised if the merge is not allowed.

    Companies with relations to another Company are not allowed to be merged. They would need to
    be manually updated in the Admin before merging.
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
            Invalid objects: {invalid_obj}""",
        )
        raise MergeNotAllowedError()

    with reversion.create_revision():
        reversion.set_comment('Company merged')
        try:
            target_changes, _ = get_planned_changes(target_company, MERGE_CONFIGURATION)
            source_changes, _ = get_planned_changes(source_company, MERGE_CONFIGURATION)
            logger.info(
                f'Target company with id: {target_company.id} relations before merge: \n'
                f'{target_changes}',
            )
            logger.info(
                f'Source company with id: {source_company.id} relations before merge: \n'
                f'{source_changes}',
            )
            results = {
                configuration.model: update_objects(configuration, source_company, target_company)
                for configuration in MERGE_CONFIGURATION
            }
        except Exception as e:
            logger.exception(f'An error occurred while merging companies: {e}')
            raise

        # As CompanyActivities are saved when an Interaction or Referral
        # automatically saved add them to the updated count.
        results[CompanyActivity] = {
            'company': results[Interaction]['company']
            + results[InvestmentProject]['investor_company']
            + results[CompanyReferral]['company'] + results[Order]['company'],
        }

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
