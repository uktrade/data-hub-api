"""Company models."""
import uuid

from django.conf import settings
from django.db import models

from datahub.company.models import Advisor
from datahub.core.models import (
    BaseModel,
)
from datahub.metadata import models as metadata_models


class CompanyExport(BaseModel):
    class ExportPotential(models.TextChoices):
        HIGH = ('high', 'High')
        MEDIUM = ('medium', 'Medium')
        LOW = ('low', 'Low')

    class ExportStatus(models.TextChoices):
        ACTIVE = ('active', 'Active')
        WON = ('won', 'Won')
        INACTIVE = ('inactive', 'Inactive')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    company = models.ForeignKey(
        'Company',
        related_name='exports',
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )

    title = models.CharField(
        blank=False,
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
    )

    owner = models.ForeignKey(
        Advisor,
        on_delete=models.CASCADE,
    )

    team_members = models.ManyToManyField(
        Advisor,
        blank=True,
        related_name='+',
    )

    # TODO - should this be a preset list in django or something in the ui?
    estimated_export_value_years = models.IntegerField()
    estimated_export_value_amount = models.DecimalField(
        max_digits=19,
        decimal_places=0,
        null=False,
        blank=False,
    )

    estimated_win_date_month = models.IntegerField(blank=False)
    estimated_win_date_year = models.IntegerField(blank=False)

    destination_country = models.ForeignKey(
        'metadata.Country',
        on_delete=models.PROTECT,
        related_name='+',
    )

    sector = models.ForeignKey(
        metadata_models.Sector,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    export_potential = models.CharField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=ExportPotential.choices,
    )

    status = models.CharField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=ExportStatus.choices,
    )

    contacts = models.ManyToManyField('company.Contact')

    # TODO - the list in datahub/company/fixtures/export_experience_categories.yaml
    # dont match the designs
    exporter_experience = models.CharField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
    )

    notes = models.TextField(null=True, blank=True)
