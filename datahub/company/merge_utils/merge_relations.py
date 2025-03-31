# Any relations in the company merge which requires additional logic when merging.
from datahub.company.merge import (
    _default_object_updater,
)
from datahub.company.models import (
    OneListCoreTeamMember,
)
from datahub.investment.opportunity.models import LargeCapitalOpportunity
from datahub.user.company_list.models import CompanyListItem, PipelineItem


def company_list_item_updater(list_item, field, target_company, source_company):
    # If there is already a list item for the target company, delete this list item instead
    # as duplicates are not allowed
    if CompanyListItem.objects.filter(list_id=list_item.list_id, company=target_company).exists():
        list_item.delete()
    else:
        _default_object_updater(list_item, field, target_company, source_company)


def one_list_core_team_member_updater(one_list_item, field, target_company, source_company):
    """The OneListCoreTeamMember model has a unique together contraint for company and adviser.

    Before copying, if the target company already contains the adviser from the source company,
    ignore it.
    """
    if OneListCoreTeamMember.objects.filter(
        adviser_id=one_list_item.adviser_id,
        company=target_company,
    ).exists():
        return
    else:
        _default_object_updater(one_list_item, field, target_company, source_company)


def large_capital_opportunity_updater(large_capital_opp, field, target_company, source_company):
    """If the LargeCapitalOpportunity already exists in the target, ignore it. Otherwise add it.
    """
    if LargeCapitalOpportunity.objects.filter(
        id=large_capital_opp.id,
        promoters__id=target_company.id,
    ).exists():
        return
    else:
        _default_object_updater(large_capital_opp, field, target_company, source_company)


def pipeline_item_updater(pipeline_item, field, target_company, source_company):
    # If there is already a pipeline item for the adviser for the target company
    # delete this item instead as the same company can't be added for the same adviser again
    if PipelineItem.objects.filter(adviser=pipeline_item.adviser, company=target_company).exists():
        pipeline_item.delete()
    else:
        _default_object_updater(pipeline_item, field, target_company, source_company)
