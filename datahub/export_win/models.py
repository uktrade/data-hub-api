from django.conf import settings

from django.db import models

from datahub.core.models import BaseOrderedConstantModel

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class BaseExportWinOrderedConstantModel(BaseOrderedConstantModel):
    """Base class for an Export Win."""

    export_win_id = models.CharField(
        max_length=MAX_LENGTH,
    )

    class Meta:
        abstract = True
        ordering = ('order', )


class TeamType(BaseExportWinOrderedConstantModel):
    """Team type"""


class HQTeamRegionOrPost(BaseExportWinOrderedConstantModel):
    """HQ Team Region or Post"""

    team_type = models.ForeignKey(
        TeamType,
        related_name='hq_team_region_or_post',
        on_delete=models.CASCADE,
    )


class WinType(BaseExportWinOrderedConstantModel):
    """Win type"""


class BusinessPotential(BaseExportWinOrderedConstantModel):
    """Business potential"""


class SupportType(BaseExportWinOrderedConstantModel):
    """Support type"""


class ExpectedValueRelation(BaseExportWinOrderedConstantModel):
    """Expected value relation"""


class ExperienceCategories(BaseExportWinOrderedConstantModel):
    """Experience categories"""


class BreakdownType(BaseExportWinOrderedConstantModel):
    """Breakdown type"""
