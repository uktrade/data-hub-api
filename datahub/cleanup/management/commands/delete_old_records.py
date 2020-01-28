from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.utils.timezone import utc

from datahub.cleanup.cleanup_config import DatetimeLessThanCleanupFilter, ModelCleanupConfig
from datahub.cleanup.management.commands._base_command import BaseCleanupCommand
from datahub.company.models import Company, Contact
from datahub.interaction.models import Interaction
from datahub.investment.project.models import InvestmentProject
from datahub.omis.order.models import Order
from datahub.omis.quote.models import Quote

COMPANY_MODIFIED_ON_CUT_OFF = datetime(2013, 8, 19, tzinfo=utc)  # 2013-08-18 + 1 day
COMPANY_EXPIRY_PERIOD = relativedelta(years=10)
CONTACT_MODIFIED_ON_CUT_OFF = datetime(2014, 7, 22, tzinfo=utc)  # 2014-07-21 + 1 day
CONTACT_EXPIRY_PERIOD = relativedelta(years=10)
INTERACTION_EXPIRY_PERIOD = relativedelta(years=10)
INVESTMENT_PROJECT_MODIFIED_ON_CUT_OFF = datetime(2013, 11, 23, tzinfo=utc)  # 2013-11-22 + 1 day
INVESTMENT_PROJECT_EXPIRY_PERIOD = relativedelta(years=10)
ORDER_MODIFIED_ON_CUT_OFF = datetime(2014, 7, 12, tzinfo=utc)  # 2014-07-11 + 1 day
ORDER_EXPIRY_PERIOD = relativedelta(years=7)
INVESTOR_PROFILE_EXPIRY_PERIOD = relativedelta(years=10)


class Command(BaseCleanupCommand):
    """Command for deleting very old records (as per the data retention policy)."""

    help = (
        'Irrevocably deletes very old records for a model, using the criteria defined in the '
        'DIT Data Hub retention policy. A simulation can be performed using the --simulate '
        'argument.'
    )

    # For each configuration, the combination of excluded_relations and the keys of
    # relation_filter_mapping should cover all related fields for the model (as
    # returned by get_related_fields()). This is to make sure that no relation is
    # missed, and there is a test that checks that all relations are covered.
    #
    # If a field should not be excluded, but should not be filtered, it should be added
    # to relation_filter_mapping with an empty list of filters.
    CONFIGS = {
        # There were multiple large bulk updates of contacts in the legacy system on and just
        # before 2013-08-18, and so modified-on dates are not reliable prior to
        # COMPANY_MODIFIED_ON_CUT_OFF.
        'company.Company': ModelCleanupConfig(
            (
                DatetimeLessThanCleanupFilter('created_on', COMPANY_EXPIRY_PERIOD),
                DatetimeLessThanCleanupFilter('modified_on', COMPANY_MODIFIED_ON_CUT_OFF),
            ),
            relation_filter_mapping={
                # Companies are not deleted if they have any related records via these relations.
                # Apart from for one_list_core_team_members, we wait for related records to expire
                # before we delete the relevant companies
                Company._meta.get_field('contacts'): (),
                Company._meta.get_field('interactions'): (),
                Company._meta.get_field('intermediate_investment_projects'): (),
                Company._meta.get_field('investee_projects'): (),
                Company._meta.get_field('investor_investment_projects'): (),
                Company._meta.get_field('one_list_core_team_members'): (),
                Company._meta.get_field('orders'): (),
                Company._meta.get_field('subsidiaries'): (),
                Company._meta.get_field('transferred_from'): (),
                Company._meta.get_field('referrals'): (),
                Company._meta.get_field('investor_profiles'): (
                    DatetimeLessThanCleanupFilter('modified_on', INVESTOR_PROFILE_EXPIRY_PERIOD),
                ),
            },
            # We want to delete the relations below along with any expired companies
            excluded_relations=(
                Company._meta.get_field('company_list_items'),
                Company._meta.get_field('export_countries'),
                Company._meta.get_field('export_countries_history'),
            ),
        ),
        # There were multiple large bulk updates of contacts in the legacy system on and just
        # before 2014-07-21, and so modified-on dates are not reliable prior to
        # CONTACT_MODIFIED_ON_CUT_OFF.
        'company.Contact': ModelCleanupConfig(
            (
                DatetimeLessThanCleanupFilter('created_on', CONTACT_EXPIRY_PERIOD),
                DatetimeLessThanCleanupFilter('modified_on', CONTACT_MODIFIED_ON_CUT_OFF),
            ),
            relation_filter_mapping={
                # Contacts are not deleted if they have any related interactions, investment
                # projects, OMIS orders or OMIS quotes. We wait for those records to expire
                # before we delete the related contacts.
                Contact._meta.get_field('interactions'): (),
                Contact._meta.get_field('investment_projects'): (),
                Contact._meta.get_field('orders'): (),
                Contact._meta.get_field('referrals'): (),
                Quote._meta.get_field('accepted_by').remote_field: (),
            },
        ),
        'company_referral.CompanyReferral': ModelCleanupConfig(
            (
                DatetimeLessThanCleanupFilter('created_on', COMPANY_EXPIRY_PERIOD),
                DatetimeLessThanCleanupFilter('modified_on', COMPANY_EXPIRY_PERIOD),
            ),
        ),
        'interaction.Interaction': ModelCleanupConfig(
            (
                DatetimeLessThanCleanupFilter('date', INTERACTION_EXPIRY_PERIOD),
            ),
            # We want to delete the relations below along with any expired interactions
            excluded_relations=(
                Interaction._meta.get_field('dit_participants'),
                Interaction._meta.get_field('export_countries'),
            ),
        ),
        # There are no investment projects in the live system with a modified-on date
        # before 2013-11-22, because of a bulk event in the legacy system (this was
        # probably when data was imported into that system from another legacy system).
        #
        # Hence, we check various other fields in addition to just modified_on as modified_on is
        # not reliable before INVESTMENT_PROJECT_MODIFIED_ON_CUT_OFF.
        'investment.InvestmentProject': ModelCleanupConfig(
            (
                DatetimeLessThanCleanupFilter(
                    'modified_on',
                    INVESTMENT_PROJECT_MODIFIED_ON_CUT_OFF,
                ),
                DatetimeLessThanCleanupFilter('created_on', INVESTMENT_PROJECT_EXPIRY_PERIOD),
                DatetimeLessThanCleanupFilter(
                    'actual_land_date',
                    INVESTMENT_PROJECT_EXPIRY_PERIOD,
                    include_null=True,
                ),
                DatetimeLessThanCleanupFilter(
                    'date_abandoned',
                    INVESTMENT_PROJECT_EXPIRY_PERIOD,
                    include_null=True,
                ),
                DatetimeLessThanCleanupFilter(
                    'date_lost',
                    INVESTMENT_PROJECT_EXPIRY_PERIOD,
                    include_null=True,
                ),
            ),
            relation_filter_mapping={
                InvestmentProject._meta.get_field('evidence_documents'): (
                    DatetimeLessThanCleanupFilter('modified_on', INVESTMENT_PROJECT_EXPIRY_PERIOD),
                ),
                InvestmentProject._meta.get_field('proposition'): (
                    DatetimeLessThanCleanupFilter('modified_on', INVESTMENT_PROJECT_EXPIRY_PERIOD),
                ),
                # We simply don't delete any records that have any interactions or are
                # referred to by another project.
                # (Instead, we wait for the referencing objects to expire themselves.)
                InvestmentProject._meta.get_field('interactions'): (),
                # The related_name for this field is '+', so we reference the field indirectly
                InvestmentProject._meta.get_field(
                    'associated_non_fdi_r_and_d_project',
                ).remote_field: (),
            },
            # These relations do not have any datetime fields to check – we just want them to be
            # deleted along with expired records.
            excluded_relations=(
                InvestmentProject._meta.get_field('team_members'),
                InvestmentProject._meta.get_field('stage_log'),
                InvestmentProject._meta.get_field('investmentprojectcode'),
                InvestmentProject._meta.get_field('activities'),
            ),
        ),
        # There are no orders in the live system with a modified-on date before
        # 2014-07-11, because of a bulk event in the legacy system (this was when
        # data was imported into that system from another legacy system).
        #
        # Hence, we check various other fields in addition to just modified_on as modified_on is
        # not reliable before ORDER_MODIFIED_ON_CUT_OFF.
        'order.Order': ModelCleanupConfig(
            (
                DatetimeLessThanCleanupFilter('modified_on', ORDER_MODIFIED_ON_CUT_OFF),
                DatetimeLessThanCleanupFilter('created_on', ORDER_EXPIRY_PERIOD),
                DatetimeLessThanCleanupFilter(
                    'completed_on',
                    ORDER_EXPIRY_PERIOD,
                    include_null=True,
                ),
                DatetimeLessThanCleanupFilter(
                    'cancelled_on',
                    ORDER_EXPIRY_PERIOD,
                    include_null=True,
                ),
            ),
            relation_filter_mapping={
                Order._meta.get_field('refunds'): (
                    DatetimeLessThanCleanupFilter('modified_on', ORDER_MODIFIED_ON_CUT_OFF),
                    DatetimeLessThanCleanupFilter('created_on', ORDER_EXPIRY_PERIOD),
                    DatetimeLessThanCleanupFilter(
                        'level2_approved_on',
                        ORDER_EXPIRY_PERIOD,
                        include_null=True,
                    ),
                ),
                Order._meta.get_field('payments'): (
                    DatetimeLessThanCleanupFilter('modified_on', ORDER_MODIFIED_ON_CUT_OFF),
                    DatetimeLessThanCleanupFilter('created_on', ORDER_EXPIRY_PERIOD),
                    # received_on is non-null
                    DatetimeLessThanCleanupFilter('received_on', ORDER_EXPIRY_PERIOD),
                ),
                Order._meta.get_field('payment_gateway_sessions'): (
                    DatetimeLessThanCleanupFilter('modified_on', ORDER_EXPIRY_PERIOD),
                ),
            },
            # These relations do not have any datetime fields to check – we just want them to be
            # deleted along with expired records.
            excluded_relations=(
                Order._meta.get_field('assignees'),
                Order._meta.get_field('subscribers'),
            ),
        ),
    }
