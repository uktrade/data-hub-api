from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.timezone import now


from model_utils import Choices


NoMatchReason = Choices(
    ('not_listed', 'The correct company is not listed, it is not possible to make a match'),
    ('more_than_one', 'There is more than one company in the list that could be a match'),
    ('not_confident', 'I am not confident to make the match'),
    ('other', 'Other'),
)


class DnBMatchingResult(models.Model):
    """
    Model containing support data for resolved D&B matching information.

    The data field can contain information about a positive match
    (e.g. duns_number) or reasons why a match can't be found
    (e.g. invalid business).
    """

    created_on = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    modified_on = models.DateTimeField(null=True, blank=True, auto_now=True)
    company = models.OneToOneField('company.Company', on_delete=models.CASCADE)
    data = JSONField(encoder=DjangoJSONEncoder)

    def __str__(self):
        """Human-friendly string representation."""
        return f'{self.company} – {self.data}'


class DnBMatchingCSVRecord(models.Model):
    """
    Model containing the actual matching data provided by D&B.

    As more iterations are planned over a long period of time (weeks),
    each batch is grouped by batch_number.
    """

    EXPECTED_DATA_FIELDS = {
        'duns_number',
        'name',
        'global_ultimate_duns_number',
        'global_ultimate_name',
        'global_ultimate_country',
        'address_1',
        'address_2',
        'address_town',
        'address_postcode',
        'address_country',
        'confidence',
        'source',
    }

    created_on = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    company_id = models.UUIDField()
    batch_number = models.PositiveIntegerField()
    data = JSONField(encoder=DjangoJSONEncoder)

    selected_duns_number = models.CharField(
        blank=True,
        null=True,
        help_text='Dun & Bradstreet unique identifier. Nine-digit number with leading zeros.',
        max_length=9,
    )

    selected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    selected_on = models.DateTimeField(null=True, blank=True)

    no_match_reason = models.CharField(
        blank=True,
        null=True,
        help_text='The reason that a match could not be found.',
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=NoMatchReason,
    )
    no_match_description = models.TextField(blank=True, null=True)

    def select_match_candidate(
        self,
        by,
        selected_duns_number,
        no_match_reason=None,
        no_match_description=None,
    ):
        """
        Select match candidate.
        If selected_duns_number is None, provide no_match_reason and no_match_description.

        :param by: the adviser who selected the match candidate
        :param selected_duns_number: duns number or None if candidate cannot be matched
        :param no_match_reason: if selected_duns_number is None, provide the reason
        :param no_match_description: if selected_duns_number is None, provide description why
        :return:
        """
        if not selected_duns_number:
            self.no_match_reason = no_match_reason
            self.no_match_description = no_match_description
        else:
            self.selected_duns_number = selected_duns_number

        self.selected_by = by
        self.selected_on = now()
        self.save()

    def save(self, *args, **kwargs):
        """
        Make sure the selected duns number exist in the data and the data contains a list
        of match candidates.
        """
        if self.data:
            if not isinstance(self.data, list):
                raise ValueError(
                    'The data must be a list of match candidates.',
                )

            if not all(row.keys() == self.EXPECTED_DATA_FIELDS for row in self.data):
                raise ValueError(
                    'The data match candidates contain unexpected fields.',
                )

        if self.selected_duns_number:
            if not any(self.selected_duns_number == row['duns_number'] for row in self.data):
                raise ValueError(
                    'Selected duns_number does not exist in the data.',
                )

        super().save(*args, **kwargs)

    def __str__(self):
        """Human-friendly string representation."""
        not_selected = '(no candidate selected)'
        selected = self.selected_duns_number if self.selected_duns_number else not_selected
        return f'{self.company_id} – {self.data} {selected}'
