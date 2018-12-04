from datetime import datetime
from typing import Any, Mapping, NamedTuple, Sequence, Union

from dateutil.relativedelta import relativedelta
from dateutil.utils import today
from django.db.models import Q
from django.utils.timezone import utc


class DatetimeLessThanCleanupFilter(NamedTuple):
    """Represents a filter in a ModelCleanupConfig."""

    # The field to use with the age threshold defined below
    date_field: str
    # Records older than this will match this filter
    age_threshold: Union[relativedelta, datetime]
    # Whether null values should be included in the filter (and considered as expired)
    include_null: bool = False

    @property
    def cut_off_date(self):
        """Absolute date to use as as the cut-off (records older than this will be deleted)."""
        if isinstance(self.age_threshold, datetime):
            return self.age_threshold

        return today(tzinfo=utc) - self.age_threshold

    def as_q(self):
        """Returns a Q object for this filter."""
        range_kwargs = {
            f'{self.date_field}__lt': self.cut_off_date,
        }
        q = Q(**range_kwargs)

        if self.include_null:
            isnull_kwargs = {
                f'{self.date_field}__isnull': True,
            }
            q |= Q(**isnull_kwargs)

        return q


class ModelCleanupConfig(NamedTuple):
    """
    Clean-up configuration for a model.

    Defines the criteria for determining which records should be cleaned up.
    """

    # The filters to apply to the model to determine the records to clean up.
    # The filters will be combined using an AND operator, so records will only be
    # cleaned up if they match all of the filters
    filters: Sequence[DatetimeLessThanCleanupFilter]
    # Fields (e.g. `Company.get_meta('interactions')`) to ignore when checking for
    # referencing objects
    excluded_relations: Sequence[Any] = ()
    # Filters that referencing objects must match (where they exist). The keys are
    # model fields e.g. Company._meta.get_field('interactions'). If multiple filters
    # are specified for a field, they are combined using the AND operator
    relation_filter_mapping: Mapping[Any, Sequence[DatetimeLessThanCleanupFilter]] = None
