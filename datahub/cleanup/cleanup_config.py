from typing import NamedTuple

from dateutil.relativedelta import relativedelta


class ModelCleanupConfig(NamedTuple):
    """
    Clean-up configuration for a model.

    Defines the criteria for determining which records should be cleaned up.
    """

    # Records older than this will be cleaned up
    age_threshold: relativedelta
    # The field to use for determining the age of a record
    date_field: str = 'modified_on'
