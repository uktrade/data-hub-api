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


class Rating(BaseExportWinOrderedConstantModel):
    """Rating"""


class Experience(BaseExportWinOrderedConstantModel):
    """Experience"""


class MarketingSource(BaseExportWinOrderedConstantModel):
    """Marketing source"""


class WithoutOurSupport(BaseExportWinOrderedConstantModel):
    """Without our support"""


class HVOProgrammes(BaseExportWinOrderedConstantModel):
    """HVO Programmes"""


class AssociatedProgramme(BaseExportWinOrderedConstantModel):
    """Associated Programme"""


class HVC(BaseExportWinOrderedConstantModel):
    """HVC codes"""

    campaign_id = models.CharField(max_length=4)
    financial_year = models.PositiveIntegerField()

    class Meta:
        ordering = ('order', )
        unique_together = ('campaign_id', 'financial_year')

    def __str__(self):
        # note name includes code
        return f'{self.name} ({self.financial_year})'

    @property
    def campaign(self):
        """
        The name of the campaign alone without the code
        e.g. Africa Agritech or Italy Automotive
        """
        # names are always <Name of HVC: HVCCode>
        return self.name.split(':')[0]

    @property
    def charcode(self):
        # see choices comment
        return f'{self.campaign_id}{self.financial_year}'

    @classmethod
    def get_by_charcode(cls, charcode):
        return cls.objects.get(campaign_id=charcode[:-2])
