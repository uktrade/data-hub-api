"""Logic for detecting probable duplicates when importing interactions.

This includes:

- duplicates of existing interactions in the database
- duplicates of other interactions in the CSV file being imported

Duplicate checking is done based on date, service and contact. These fields were chosen for
simplicity, and because we are primarily dealing with overseas delivery partner interactions
which have specific services and are only created by importing CSV files.
"""

from datahub.interaction.models import Interaction

# They keys of this mapping correspond the cleaned data of an InteractionCSVRowForm and are used
# to determine if an interaction is a duplicate.
#
# For example, if two contacts have the same date, contact and service they are considered a
# duplicate.
#
# The values are field lookups for the Interaction model.
#
# (Note that the date field on the model is a DateTime field – only the date part is considered
# when checking if a row is a duplicate of existing interactions.)
DUPLICATE_FIELD_MAPPING = {
    'date': 'date__date',
    'contact': 'contacts',
    'service': 'service',
}


def is_duplicate_of_existing_interaction(cleaned_data):
    """Check if a cleaned InteractionCSVRowForm is a duplicate of an existing interaction in the
    database.

    The query appears to be fairly fast, and makes use of existing indexes.
    """
    if not _cleaned_data_to_key(cleaned_data):
        return False

    filter_kwargs = {
        queryset_field: cleaned_data[data_field]
        for data_field, queryset_field in DUPLICATE_FIELD_MAPPING.items()
    }

    return Interaction.objects.filter(**filter_kwargs).exists()


class DuplicateTracker:
    """Used to detect rows that are duplicates of another row in an interactions CSV file
    that is being imported.
    """

    def __init__(self):
        """Initialise the instance."""
        self.item_keys = set()

    def add_item(self, cleaned_data):
        """Add the cleaned data of a InteractionCSVRowForm to the collection of rows seen so far."""
        key = _cleaned_data_to_key(cleaned_data)
        if key:
            self.item_keys.add(key)

    def has_item(self, cleaned_data):
        """Check if a InteractionCSVRowForm is a duplicate of a previously-added row."""
        key = _cleaned_data_to_key(cleaned_data)
        return key and key in self.item_keys


def _cleaned_data_to_key(cleaned_data):
    """Return a tuple representing a unique key for the cleaned data of an InteractionCSVRowForm."""
    # As an optimisation we could just track the pk for model instances,
    # but that is omitted for simplicity
    key = tuple(cleaned_data.get(field) for field in DUPLICATE_FIELD_MAPPING)

    if all(key):
        return key

    # Some of the fields are missing (this happens if they did not pass validation)
    return None
