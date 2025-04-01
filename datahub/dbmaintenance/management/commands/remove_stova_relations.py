from logging import getLogger

import reversion
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.management.base import BaseCommand
from django.db import transaction

from datahub.company.models import Company, Contact
from datahub.company_activity.models import StovaAttendee, TempRelationStorage
from datahub.interaction.models import Interaction

logger = getLogger(__name__)


class Command(BaseCommand):
    """Command to remove contacts, companies and interactions created from Stova.

    Uses TempRelationStorage model to track object IDs which have been deleted. This will make it
    possible to restore them by their ID from reversion.
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
        parser.add_argument('batch_size', type=int, nargs='?', default=5000)

    def handle(self, *args, **options):
        """Process the CSV file and logs some additional logging to help with the company duns update.
        """
        is_simulation = options['simulate']
        batch_size = options['batch_size']
        logger.info(f'Simulation is: {is_simulation}')

        self.delete_interactions(is_simulation, batch_size)
        self.delete_contacts(is_simulation, batch_size)
        self.delete_companies(is_simulation, batch_size)

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

    def delete_interactions(self, is_simulation: bool, batch_size: int) -> None:
        """Delete each Interaction one at a time to process signals and catch each deletion
        fail individually.

        :param is_simulation: If True, does not perform deletions and only logs. If False deletes
            from DB.
        :param batch_size: How many records to delete at a time.
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
            .distinct()[:batch_size]
        )
        logger.info(f'About to delete {interactions.count()} interactions created from Stova')
        self.removal_log['interaction_removal_log']['to_delete'] = interactions.count()

        interactions_deleted = 0
        for interaction in interactions:
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
                        interaction_id = interaction.id
                        interaction.delete()
                        interactions_deleted += 1
                        self.removal_log['interaction_removal_log']['deleted'] = (
                            interactions_deleted
                        )
                        # For restoring by ID from reversion.
                        if not TempRelationStorage.objects.filter(
                            model_name='Interaction',
                            object_id=interaction_id,
                        ).exists():
                            TempRelationStorage.objects.create(
                                model_name='Interaction',
                                object_id=interaction_id,
                            )
                        if is_simulation:
                            # Raising an error rolls the transaction back
                            raise Exception("Simulating, don't delete.")
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

    def delete_contacts(self, is_simulation: bool, batch_size: int) -> None:
        """Delete each Contact one at a time to process signals and catch each deletion
        fail individually.

        :param is_simulation: If True, does not perform deletions and only logs. If False deletes
            from DB.
        :param batch_size: How many records to delete at a time.
        :returns: List of contact deletion failures or empty list if there are none.
        """
        stova_contacts = Contact.objects.filter(source='Stova')[:batch_size]
        logger.info(f'About to delete {stova_contacts.count()} contacts created from Stova')
        self.removal_log['contact_removal_log']['to_delete'] = stova_contacts.count()

        contacts_deleted = 0
        for contact in stova_contacts:
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
                        contact_id = contact.id
                        contact.delete()
                        contacts_deleted += 1
                        self.removal_log['contact_removal_log']['deleted'] = contacts_deleted
                        if is_simulation:
                            # Raising an error rolls the transaction back
                            raise Exception("Simulating, don't delete.")
                        # For restoring by ID from reversion.
                        if not TempRelationStorage.objects.filter(
                            model_name='Contact',
                            object_id=contact_id,
                        ).exists():
                            TempRelationStorage.objects.create(
                                model_name='Contact',
                                object_id=contact_id,
                            )
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

    def delete_companies(self, is_simulation: bool, batch_size: int) -> None:
        """Delete each Company one at a time to process signals and catch each deletion
        fail individually.

        :param is_simulation: If True, does not perform deletions and only logs. If False deletes
            from DB.
        :param batch_size: How many records to delete at a time.
        :returns: List of company deletion failures or empty list if there are none.
        """
        stova_companies = Company.objects.filter(source='Stova')[:batch_size]
        logger.info(f'About to delete {stova_companies.count()} companies created from Stova')
        self.removal_log['company_removal_log']['to_delete'] = stova_companies.count()

        companies_deleted = 0
        for company in stova_companies:
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
                        company_id = company.id
                        company.delete()
                        companies_deleted += 1
                        self.removal_log['company_removal_log']['deleted'] = companies_deleted
                        if is_simulation:
                            # Raising an error rolls the transaction back
                            raise Exception("Simulating, don't delete.")
                        # For restoring by ID from reversion.
                        if not TempRelationStorage.objects.filter(
                            model_name='Company',
                            object_id=company_id,
                        ).exists():
                            TempRelationStorage.objects.create(
                                model_name='Company',
                                object_id=company_id,
                            )
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
