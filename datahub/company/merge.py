from collections import namedtuple

from django.db import transaction

from datahub.company.models import Company, Contact
from datahub.interaction.models import Interaction

MoveEntry = namedtuple(
    'MoveEntry',
    [
        'count',
        'model_meta',
    ],
)


MergeResult = namedtuple(
    'MergeResult',
    [
        'num_interactions_moved',
        'num_contacts_moved',
    ],
)


class DuplicateCompanyMerger:
    """Utility class for merging duplicate companies."""

    def __init__(self, source_company: Company, target_company: Company):
        """Initialises the instance with the source and target companies."""
        self.source_company = source_company
        self.target_company = target_company

    def get_planned_changes(self):
        """Gets information about the changes that would be made if the merge proceeds."""
        move_entries = []

        contact_count = self.source_company.contacts.count()
        self._append_move_entry(move_entries, contact_count, Contact)

        interaction_count = self.source_company.interactions.count()
        self._append_move_entry(move_entries, interaction_count, Interaction)

        should_archive_source = not self.source_company.archived

        return move_entries, should_archive_source

    def is_merge_allowed(self):
        """Returns whether the merge is allowed."""
        return (
            self.source_company.is_valid_merge_source
            and self.target_company.is_valid_merge_target
        )

    @transaction.atomic
    def perform_merge(self, user):
        """Merges the source company into the target company."""
        num_interactions_moved = 0
        num_contacts_moved = 0

        for interaction in self.source_company.interactions.iterator():
            interaction.company = self.target_company
            interaction.save(update_fields=('company',))
            num_interactions_moved += 1

        for contact in self.source_company.contacts.iterator():
            contact.company = self.target_company
            contact.save(update_fields=('company',))
            num_contacts_moved += 1

        self.source_company.mark_as_transferred(
            self.target_company,
            Company.TRANSFER_REASONS.duplicate,
            user,
        )

        return MergeResult(num_interactions_moved, num_contacts_moved)

    @staticmethod
    def _append_move_entry(to_move, count, model):
        if count == 0:
            return

        move_item = MoveEntry(count, model._meta)
        to_move.append(move_item)
