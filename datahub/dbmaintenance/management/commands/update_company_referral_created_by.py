from logging import getLogger

from django.core.management.base import BaseCommand

import reversion

from django.db import transaction

from datahub.company.models import Advisor
from datahub.company_referral.models import CompanyReferral


logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to set referral.created_by where incorrect.

    Some referral records have incorrect created_by values which
    is set as the default value for sending advisor. This changes the created_by value
    """

    def add_arguments(self, parser):
        parser.add_argument('referral_id', type=str, help='UUID of the referral')
        parser.add_argument('user_id', type=str, help='UUID of the advisor')

    @transaction.atomic
    def handle(self, *args, **options):
        referral_id = options['referral_id']
        user_id = options['user_id']

        try:
            referral = CompanyReferral.objects.get(id=referral_id)
            user = Advisor.objects.get(id=user_id)
        except Advisor.DoesNotExist as e:
            self.stderr.write(self.style.ERROR(str(e)))
            return

        referral.created_by = user

        with reversion.create_revision():
            referral.save(update_fields=('created_by',))
            reversion.set_comment(
                'Created by updated to new id.',
            )

        self.stdout.write(self.style.SUCCESS(
            f'Updated referral created_by for --{referral}-- to the id: {user}',
        ))
