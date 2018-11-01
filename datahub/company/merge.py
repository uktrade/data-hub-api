from collections import namedtuple

from datahub.company.models import Contact
from datahub.interaction.models import Interaction


MoveEntry = namedtuple(
    'MoveEntry',
    [
        'count',
        'model_meta',
    ],
)


class DuplicateCompanyMerger:
    """Utility class for merging duplicate companies."""

    def __init__(self, source_company, target_company):
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

    @staticmethod
    def _append_move_entry(to_move, count, model):
        if count == 0:
            return

        move_item = MoveEntry(count, model._meta)
        to_move.append(move_item)
