from logging import getLogger

import reversion

from django.contrib.postgres.aggregates import ArrayAgg
from django.core.management.base import BaseCommand

from datahub.company.models import Company, Contact
from datahub.company_activity.models import StovaAttendee
from datahub.interaction.models import Interaction


logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to remove contacts, companies and interactions created from Stova.
    """

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

        interaction_delete_failures = self.delete_interactions(is_simulation)
        contact_delete_failures = self.delete_contacts(is_simulation)
        company_delete_failures = self.delete_companies(is_simulation)

        logger.info(interaction_delete_failures)
        logger.info(contact_delete_failures)
        logger.info(company_delete_failures)

        logger.info(f'There were {len(interaction_delete_failures)} interaction deletion failures')
        logger.info(f'There were {len(contact_delete_failures)} contact deletion failures')
        logger.info(f'There were {len(company_delete_failures)} company deletion failures')

    def delete_interactions(self, is_simulation: bool) -> list:
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

        interactions_to_delete = 0
        interactions_with_more_than_one_contact = 0
        failures = []
        for interaction in interactions:
            interactions_to_delete += 1

            if is_simulation:
                continue

            # Modify the fields to create revisions. Without this the delete cannot be
            # reverted to the previous state.
            with reversion.create_revision():
                interaction.archived_reason = 'About to be deleted'
                interaction.save()
                reversion.set_comment('Interaction deletion as created from Stova.')

            try:
                interaction.delete()
            except Exception as error:
                failures.append(
                    {
                        'interaction_id': interaction.id,
                        'error': error,
                    },
                )

        logger.info(
            f'There were {interactions_with_more_than_one_contact} with more than one contact',
        )
        logger.info(f'Deleted {interactions_to_delete} interactions')
        return failures

    def delete_contacts(self, is_simulation: bool) -> dict:
        """
        Delete each Contact one at a time to process signals and catch each deletion
        fail individually.

        :param is_simulation: If True, does not perform deletions and only logs. If False deletes
            from DB.
        :returns: List of contact deletion failures or empty list if there are none.
        """
        stova_contacts = Contact.objects.filter(source='Stova')
        logger.info(f'About to delete {stova_contacts.count()} contacts created from Stova')

        contacts_to_delete = 0
        failures = []
        for contact in stova_contacts:
            contacts_to_delete += 1

            if is_simulation:
                continue

            # Modify the fields to create revisions. Without this the delete cannot be
            # reverted to the previous state.
            with reversion.create_revision():
                contact.archived_reason = 'About to be deleted'
                contact.save()
                reversion.set_comment('Contact deletion as created from Stova.')

            try:
                contact.delete()
            except Exception as error:
                failures.append(
                    {
                        'contact_id': contact.id,
                        'error': error,
                    },
                )

        return failures

    def delete_companies(self, is_simulation: bool) -> dict:
        """
        Delete each Company one at a time to process signals and catch each deletion
        fail individually.

        :param is_simulation: If True, does not perform deletions and only logs. If False deletes
            from DB.
        :returns: List of company deletion failures or empty list if there are none.
        """
        stova_companies = Company.objects.filter(source='Stova')
        logger.info(f'About to delete {stova_companies.count()} companies created from Stova')

        companies_to_delete = 0
        failures = []
        for company in stova_companies:
            companies_to_delete += 1

            if is_simulation:
                continue

            # Modify the fields to create revisions. Without this the delete cannot be
            # reverted to the previous state.
            with reversion.create_revision():
                company.archived_reason = 'About to be deleted'
                company.save()
                reversion.set_comment('Company deletion as created from Stova.')

            try:
                company.delete()
            except Exception as error:
                failures.append(
                    {
                        'company_id': company.id,
                        'error': error,
                    },
                )

        return failures
