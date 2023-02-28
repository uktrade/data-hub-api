"""Export models."""
import uuid

from django.conf import settings
from django.db import models

from datahub.company.models import Advisor, Company, Contact
from datahub.core import reversion
from datahub.core.models import ArchivableModel, BaseModel, BaseOrderedConstantModel
from datahub.metadata import models as metadata_models

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class ExportExperience(BaseOrderedConstantModel):
    """Export experience"""


class ExportYear(BaseOrderedConstantModel):
    """Export year"""


@reversion.register_base_model()
class CompanyExport(ArchivableModel, BaseModel):
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
        Company,
        related_name='exports',
        blank=False,
        on_delete=models.PROTECT,
    )

    title = models.CharField(
        blank=False,
        max_length=MAX_LENGTH,
    )

    owner = models.ForeignKey(
        Advisor,
        blank=False,
        on_delete=models.PROTECT,
    )

    team_members = models.ManyToManyField(
        Advisor,
        blank=True,
        related_name='+',
    )

    estimated_export_value_years = models.ForeignKey(
        ExportYear,
        blank=False,
        on_delete=models.PROTECT,
    )

    estimated_export_value_amount = models.DecimalField(
        max_digits=19,
        decimal_places=0,
        blank=False,
    )

    estimated_win_date = models.DateTimeField(
        blank=False,
    )

    destination_country = models.ForeignKey(
        metadata_models.Country,
        blank=False,
        on_delete=models.PROTECT,
        related_name='+',
    )

    sector = models.ForeignKey(
        metadata_models.Sector,
        blank=False,
        on_delete=models.PROTECT,
    )

    export_potential = models.CharField(
        max_length=MAX_LENGTH,
        choices=ExportPotential.choices,
        blank=False,
    )

    status = models.CharField(
        max_length=MAX_LENGTH,
        choices=ExportStatus.choices,
        default=ExportStatus.ACTIVE,
        blank=False,
    )

    contacts = models.ManyToManyField(
        Contact,
        blank=False,
        related_name='exports',
    )

    exporter_experience = models.ForeignKey(
        ExportExperience,
        blank=False,
        on_delete=models.PROTECT,
    )

    notes = models.TextField(
        blank=True,
    )

    def __str__(self):
        """Admin displayed human readable name."""
        return self.title
