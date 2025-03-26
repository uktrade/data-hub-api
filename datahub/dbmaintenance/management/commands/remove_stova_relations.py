from logging import getLogger

import reversion

from django.contrib.postgres.aggregates import ArrayAgg
from django.core.management.base import BaseCommand
from django.db import transaction

from datahub.company.models import Company, Contact
from datahub.company_activity.models import StovaAttendee
from datahub.interaction.models import Interaction


logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to remove contacts, companies and interactions created from Stova.
    """

    removal_log: dict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.removal_log = {
            'interaction_removal_log': {'to_delete': 0, 'deleted': 0, 'errors': []},
            'contact_removal_log': {'to_delete': 0, 'deleted': 0, 'errors': []},
            'company_removal_log': {'to_delete': 0, 'deleted': 0, 'errors': []},
        }

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            '--simulate',
            action='store_true',
            help='Simulate the command and only log expected changes without doing the change.',
        )

    def handle(self, *args, **options):
        """
        Process the CSV file and logs some additional logging to help with the company duns update.
        """
        is_simulation = options['simulate']
        logger.info(f'Simulation is: {is_simulation}')

        self.delete_interactions(is_simulation)
        self.delete_contacts(is_simulation)
        self.delete_companies(is_simulation)

        logger.info(self.removal_log['interaction_removal_log']['errors'])
        logger.info(self.removal_log['contact_removal_log']['errors'])
        logger.info(self.removal_log['company_removal_log']['errors'])

        logger.info(
            f'There were {len(self.removal_log["interaction_removal_log"]["errors"])} '
            'interaction deletion failures',
        )
        logger.info(
            f'There were {len(self.removal_log["contact_removal_log"]["errors"])} contact '
            'deletion failures',
        )
        logger.info(
            f'There were {len(self.removal_log["company_removal_log"]["errors"])} company '
            'deletion failures',
        )

        logger.info(
            f'There were {self.removal_log["interaction_removal_log"]["deleted"]} interactions '
            f'deleted out of {self.removal_log["interaction_removal_log"]["to_delete"]}',
        )
        logger.info(
            f'There were {self.removal_log["contact_removal_log"]["deleted"]} contacts deleted '
            f'out of {self.removal_log["contact_removal_log"]["to_delete"]}',
        )
        logger.info(
            f'There were {self.removal_log["company_removal_log"]["deleted"]} companies deleted '
            f'out of {self.removal_log["company_removal_log"]["to_delete"]}',
        )

    def delete_interactions(self, is_simulation: bool) -> None:
        """
        Delete each Interaction one at a time to process signals and catch each deletion
        fail individually.

        :param is_simulation: If True, does not perform deletions and only logs. If False deletes
            from DB.
        :returns: List of interaction deletion failures or empty list if there are none.
        """
        stova_attendee_contact_ids = set(
            StovaAttendee.objects.all().values_list('contact_id', flat=True),
        )
        interactions = (
            Interaction.objects.filter(
                service_id='f6671176-6493-43ba-a92d-899281efcb55',  # Stova only interaction
                contacts__in=stova_attendee_contact_ids,
            )
            .annotate(contact_ids=ArrayAgg('contacts'))
            .distinct()
        )
        logger.info(f'About to delete {interactions.count()} interactions created from Stova')
        self.removal_log['interaction_removal_log']['to_delete'] = interactions.count()

        interactions_deleted = 0
        for interaction in interactions:
            if is_simulation:
                continue

            # Double try/except, outer to catch inner. Inner to rollback the transaction and
            # prevent save to the archived_reason field. Outer to still continue deleting the
            # remaining fields.
            try:
                with transaction.atomic():
                    # Modify the fields to create revisions. Without this the delete cannot be
                    # reverted to the previous state.
                    with reversion.create_revision():
                        interaction.archived_reason = 'About to be deleted'
                        interaction.save()
                        reversion.set_comment('Interaction deletion as created from Stova.')

                    try:
                        interaction.delete()
                        interactions_deleted += 1
                        self.removal_log['interaction_removal_log']['deleted'] = (
                            interactions_deleted
                        )
                    except Exception as error:
                        self.removal_log['interaction_removal_log']['errors'].append(
                            {
                                'interaction_id': interaction.id,
                                'error': error,
                            },
                        )
                        raise
            except Exception:
                continue

    def delete_contacts(self, is_simulation: bool) -> None:
        """
        Delete each Contact one at a time to process signals and catch each deletion
        fail individually.

        :param is_simulation: If True, does not perform deletions and only logs. If False deletes
            from DB.
        :returns: List of contact deletion failures or empty list if there are none.
        """
        stova_contacts = Contact.objects.filter(source='Stova')
        logger.info(f'About to delete {stova_contacts.count()} contacts created from Stova')
        self.removal_log['contact_removal_log']['to_delete'] = stova_contacts.count()

        contacts_deleted = 0
        for contact in stova_contacts:
            if is_simulation:
                continue

            # Double try/except, outer to catch inner. Inner to rollback the transaction and
            # prevent save to the archived_reason field. Outer to still continue deleting the
            # remaining fields.
            try:
                with transaction.atomic():
                    # Modify the fields to create revisions. Without this the delete cannot be
                    # reverted to the previous state.
                    with reversion.create_revision():
                        contact.archived_reason = 'About to be deleted'
                        contact.save()
                        reversion.set_comment('Contact deletion as created from Stova.')

                    try:
                        contact.delete()
                        contacts_deleted += 1
                        self.removal_log['contact_removal_log']['deleted'] = contacts_deleted
                    except Exception as error:
                        self.removal_log['contact_removal_log']['errors'].append(
                            {
                                'contact_id': contact.id,
                                'error': error,
                            },
                        )
                        raise
            except Exception:
                continue

    def delete_companies(self, is_simulation: bool) -> None:
        """
        Delete each Company one at a time to process signals and catch each deletion
        fail individually.

        :param is_simulation: If True, does not perform deletions and only logs. If False deletes
            from DB.
        :returns: List of company deletion failures or empty list if there are none.
        """
        stova_companies = Company.objects.filter(source='Stova')
        logger.info(f'About to delete {stova_companies.count()} companies created from Stova')
        self.removal_log['company_removal_log']['to_delete'] = stova_companies.count()

        companies_deleted = 0
        for company in stova_companies:
            if is_simulation:
                continue

            # Double try/except, outer to catch inner. Inner to rollback the transaction and
            # prevent save to the archived_reason field. Outer to still continue deleting the
            # remaining fields.
            try:
                with transaction.atomic():
                    # Modify the fields to create revisions. Without this the delete cannot be
                    # reverted to the previous state.
                    with reversion.create_revision():
                        company.archived_reason = 'About to be deleted'
                        company.save()
                        reversion.set_comment('Company deletion as created from Stova.')

                    try:
                        company.delete()
                        companies_deleted += 1
                        self.removal_log['company_removal_log']['deleted'] = companies_deleted
                    except Exception as error:
                        self.removal_log['company_removal_log']['errors'].append(
                            {
                                'company_id': company.id,
                                'error': error,
                            },
                        )
                        raise
            except Exception:
                continue
