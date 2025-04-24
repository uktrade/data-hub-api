import uuid
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from datahub.company.models.company import Company
from datahub.core import reversion
from datahub.core.models import ArchivableModel, BaseModel

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@reversion.register_base_model()
class KingsAwardRecipient(ArchivableModel, BaseModel):
    """A King's Award for Enterprise recipient."""

    MIN_YEAR = 1966
    MAX_YEAR_AWARDED_LOOK_AHEAD = 1
    MAX_YEAR_EXPIRED_LOOK_AHEAD = 6

    @classmethod
    def get_max_year(cls, look_ahead_years):
        """Calculate the maximum allowable year based on current year plus a
        look-ahead (years). Used for validating year_awarded and year_expired
        fields.
        """
        return datetime.now().year + look_ahead_years

    class Category(models.TextChoices):
        INTERNATIONAL_TRADE = (
            'International Trade (Export)',
            'International Trade (Export)',
        )
        INNOVATION = (
            'Innovation (Technology)',
            'Innovation (Technology)',
        )
        EXPORT_AND_TECHNOLOGY = (
            'Export and Technology (Combined)',
            'Export and Technology (Combined)',
        )
        SUSTAINABLE_DEVELOPMENT = (
            'Sustainable Development (Environmental Achievement)',
            'Sustainable Development (Environmental Achievement)',
        )
        PROMOTING_OPPORTUNITY = (
            'Promoting Opportunity (Through Social Mobility)',
            'Promoting Opportunity (Through Social Mobility)',
        )

        @classmethod
        def from_alias(cls, alias):
            try:
                return cls.alias_mapping[alias.lower()]
            except KeyError:
                raise ValueError(f"Invalid category alias: '{alias}'")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='kings_awards')

    year_awarded = models.PositiveIntegerField(validators=[MinValueValidator(MIN_YEAR)])
    category = models.CharField(max_length=MAX_LENGTH, choices=Category.choices)
    citation = models.TextField(null='', blank=True)

    year_expired = models.PositiveIntegerField(validators=[MinValueValidator(MIN_YEAR)])

    class Meta:
        verbose_name = "King's Award"
        verbose_name_plural = "King's Awards"
        unique_together = ('company', 'category', 'year_awarded')
        indexes = [
            models.Index(fields=['company', 'year_awarded']),
            models.Index(fields=['category', 'year_awarded']),
        ]

    def __str__(self):
        return f'{self.company.name} - {self.year_awarded} {self.get_category_display()}'

    def clean(self):
        """Custom validation to be ran at model.full_clean()."""
        super().clean()

        max_year_awarded = self.get_max_year(look_ahead_years=self.MAX_YEAR_AWARDED_LOOK_AHEAD)
        max_year_expired = self.get_max_year(look_ahead_years=self.MAX_YEAR_EXPIRED_LOOK_AHEAD)

        if self.year_awarded > max_year_awarded:
            raise ValidationError(
                {'year_awarded': f'Year cannot be greater than {max_year_awarded}'},
            )
        if self.year_expired > max_year_expired:
            raise ValidationError(
                {'year_expired': f'Year cannot be greater than {max_year_expired}'},
            )
        if self.year_awarded > self.year_expired:
            raise ValidationError(
                {
                    'year_expired': f'Year awarded {self.year_awarded} cannot be after year expired {self.year_expired}',
                },
            )


KingsAwardRecipient.Category.alias_mapping = {
    'international-trade': KingsAwardRecipient.Category.INTERNATIONAL_TRADE,
    'innovation': KingsAwardRecipient.Category.INNOVATION,
    'export-and-technology': KingsAwardRecipient.Category.EXPORT_AND_TECHNOLOGY,
    'sustainable-development': KingsAwardRecipient.Category.SUSTAINABLE_DEVELOPMENT,
    'promoting-opportunity': KingsAwardRecipient.Category.PROMOTING_OPPORTUNITY,
}
