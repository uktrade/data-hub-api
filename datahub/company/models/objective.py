import uuid

from django.conf import settings
from django.db import models
from django.core.validators import MaxValueValidator

from datahub.company.models import Company

from datahub.core import reversion

from datahub.core.models import ArchivableModel, BaseModel
MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH

@reversion.register_base_model()
class Objective(ArchivableModel, BaseModel):
    """Representation of a company objective."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    company = models.ForeignKey(
        Company,
        related_name='company_objective',
        on_delete=models.PROTECT,
    )
    subject = models.CharField(max_length=MAX_LENGTH, null=True)
    detail = models.TextField(null=True)
    target_date = models.DateField()
    has_blocker = models.BooleanField(
        null=True,
        blank=True,
    )
    blocker_description = models.TextField(blank=True, null=True)
    progress = models.PositiveIntegerField(
        validators=[
            MaxValueValidator(100),
        ]
    )