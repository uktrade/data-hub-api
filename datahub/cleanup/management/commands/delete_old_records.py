from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.utils.timezone import utc

from datahub.cleanup.cleanup_config import DatetimeLessThanCleanupFilter, ModelCleanupConfig
from datahub.cleanup.management.commands._base_command import BaseCleanupCommand
from datahub.omis.order.models import Order


INTERACTION_EXPIRY_PERIOD = relativedelta(years=10)
ORDER_MODIFIED_ON_CUT_OFF = datetime(2014, 7, 12, tzinfo=utc)  # 2014-07-11 + 1 day
ORDER_EXPIRY_PERIOD = relativedelta(years=7)


class Command(BaseCleanupCommand):
    """Command for deleting very old records (as per the data retention policy)."""

    help = (
        'Irrevocably deletes very old records for a model, using the criteria defined in the '
        'DIT Data Hub retention policy. A simulation can be performed using the --simulate '
        'argument.'
    )

    CONFIGS = {
        'interaction.Interaction': ModelCleanupConfig(
            (
                DatetimeLessThanCleanupFilter('date', INTERACTION_EXPIRY_PERIOD),
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
