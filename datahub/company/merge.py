from collections import namedtuple

from django.db import transaction

from datahub.company.models import Company, Contact
from datahub.core.exceptions import DataHubException
from datahub.core.model_helpers import get_related_fields, get_self_referential_relations
from datahub.interaction.models import Interaction

ALLOWED_RELATIONS_FOR_MERGING = {
    Company._meta.get_field('dnbmatchingresult').remote_field,
    Contact.company.field,
    Interaction.company.field,
}


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


class MergeNotAllowedError(DataHubException):
    """Merging the specified source company into the specified target company is not allowed."""


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

    def is_source_valid(self):
        """
        Returns whether the specified source company is a valid merge source.

        This checks whether there are any references to the source company (other than
        references through the relations specified in ALLOWED_RELATIONS_FOR_MERGING).
        It also checks if the source company has any references to other companies.
        Merging is not permitted if either of those types of reference exists.
        """
        if not hasattr(self, '_cached_is_source_valid'):
            self._cached_is_source_valid = self._is_source_valid()

        return self._cached_is_source_valid

    def is_target_valid(self):
        """
        Returns whether the specified target company is a valid merge target.

        This checks that the target company isn't archived.
        """
        return not self.target_company.archived

    def is_valid(self):
        """Returns whether the merge is allowed."""
        return self.is_source_valid() and self.is_target_valid()

    @transaction.atomic
    def perform_merge(self, user):
        """
        Merges the source company into the target company.

        is_valid() should be called first to check if the merge is allowed. DataHubException
        will be raised if the merge is not allowed, and perform_merge() was called anyway.
        """
        if not self.is_valid():
            raise MergeNotAllowedError()

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

        self.source_company.modified_by = user
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

    def _is_source_valid(self):
        # First, check that there are no references to the source company from other objects
        # (other than via the fields specified in ALLOWED_RELATIONS_FOR_MERGING).
        relations = get_related_fields(Company)

        has_related_objects = any(
            getattr(self.source_company, relation.name).count()
            for relation in relations
            if relation.remote_field not in ALLOWED_RELATIONS_FOR_MERGING
        )

        if has_related_objects:
            return False

        # Then, check that the source company itself doesn't have any references to other
        # companies.
        self_referential_fields = get_self_referential_relations(Company)
        return not any(
            getattr(self.source_company, field.name) for field in self_referential_fields
        )
