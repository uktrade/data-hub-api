from functools import lru_cache

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.investment.models import InvestmentProject
from datahub.metadata.models import ReferralSourceActivity, ReferralSourceMarketing


class Command(CSVBaseCommand):
    """Command to update investment_project.referral_source_activity/_marketing."""

    @lru_cache(maxsize=None)
    def get_referral_source_activity(self, referral_source_activity_id):
        """
        :param referral_source_activity_id: uuid of the referral source activity
        :return: instance of ReferralSourceActivity
                with id == referral_source_activity_id if it exists,
                None otherwise
        """
        if (
            not referral_source_activity_id or
            referral_source_activity_id.lower().strip() == 'null'
        ):
            return None
        return ReferralSourceActivity.objects.get(id=referral_source_activity_id)

    @lru_cache(maxsize=None)
    def get_referral_source_activity_marketing(self, referral_source_activity_marketing_id):
        """
        :param referral_source_activity_marketing_id: uuid of the referral source marketing
        :return: instance of ReferralSourceMarketing
                with id == referral_source_activity_marketing_id if it exists,
                None otherwise
        """
        if (
            not referral_source_activity_marketing_id or
            referral_source_activity_marketing_id.lower().strip() == 'null'
        ):
            return None
        return ReferralSourceMarketing.objects.get(id=referral_source_activity_marketing_id)

    def _should_update(
        self,
        investment_project,
        referral_source_activity,
        referral_source_activity_marketing,
    ):
        """
        Checks if Investment project should be updated.

        :param investment_project: instance of InvestmentProject
        :param referral_source_activity: instance of ReferralSourceActivity or None
        :param referral_source_activity_marketing:
                instance of ReferralSourceMarketing or None
        :return: True if investment project needs to be updated
        """
        return (
            investment_project.referral_source_activity_id !=
            referral_source_activity.id or
            investment_project.referral_source_activity_marketing_id !=
            referral_source_activity_marketing.id
        )

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        investment_project = InvestmentProject.objects.get(pk=row['id'])

        referral_source_activity = self.get_referral_source_activity(
            row['referral_source_activity_id'],
        )

        referral_source_activity_marketing = self.get_referral_source_activity_marketing(
            row['referral_source_activity_marketing_id'],
        )

        if self._should_update(
            investment_project,
            referral_source_activity,
            referral_source_activity_marketing,
        ):
            investment_project.referral_source_activity = \
                referral_source_activity
            investment_project.referral_source_activity_marketing = \
                referral_source_activity_marketing

            if not simulate:
                with reversion.create_revision():
                    investment_project.save(
                        update_fields=(
                            'referral_source_activity',
                            'referral_source_activity_marketing',
                        ),
                    )
                    reversion.set_comment('ReferralSourceActivityMarketing migration.')
