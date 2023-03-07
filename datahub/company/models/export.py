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
    """A export item for a company"""

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
        related_name='company_exports',
        on_delete=models.PROTECT,
    )

    title = models.CharField(
        max_length=MAX_LENGTH,
    )

    owner = models.ForeignKey(
        Advisor,
        on_delete=models.PROTECT,
        related_name='owner_exports',
    )

    team_members = models.ManyToManyField(
        Advisor,
        blank=True,
        related_name='team_exports',
    )

    estimated_export_value_years = models.ForeignKey(
        ExportYear,
        on_delete=models.PROTECT,
        related_name='+',
    )

    estimated_export_value_amount = models.DecimalField(
        max_digits=19,
        decimal_places=0,
    )

    estimated_win_date = models.DateTimeField()

    destination_country = models.ForeignKey(
        metadata_models.Country,
        on_delete=models.PROTECT,
        related_name='+',
    )

    sector = models.ForeignKey(
        metadata_models.Sector,
        on_delete=models.PROTECT,
        related_name='+',
    )

    export_potential = models.CharField(
        max_length=MAX_LENGTH,
        choices=ExportPotential.choices,
    )

    status = models.CharField(
        max_length=MAX_LENGTH,
        choices=ExportStatus.choices,
        default=ExportStatus.ACTIVE,
    )

    contacts = models.ManyToManyField(
        Contact,
        related_name='contact_exports',
    )

    exporter_experience = models.ForeignKey(
        ExportExperience,
        on_delete=models.PROTECT,
        related_name='+',
    )

    notes = models.TextField(
        blank=True,
    )

    def __str__(self):
        """Admin displayed human readable name."""
        return self.title
