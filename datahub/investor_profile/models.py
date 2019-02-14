import uuid

from django.db import models

from datahub.core import reversion
from datahub.core.models import (
    BaseModel,
)


@reversion.register_base_model()
class InvestorProfile(BaseModel):
    """Investor profile model"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
    )

    investor_company = models.ForeignKey(
        'company.Company',
        related_name='investor_profiles',
        on_delete=models.CASCADE,
    )

    profile_type = models.ForeignKey(
        'ProfileType',
        related_name='+',
        on_delete=models.PROTECT,
    )

    class Meta:
        unique_together = ('investor_company', 'profile_type')


