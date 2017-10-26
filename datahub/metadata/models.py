from django.contrib.auth.models import Group
from django.db import models
from django.utils.translation import ugettext_lazy as _

from datahub.core.models import BaseConstantModel, BaseOrderedConstantModel


class BusinessType(BaseConstantModel):
    """Company business type."""

    pass


class Sector(BaseConstantModel):
    """Company sector."""

    pass


class EmployeeRange(BaseOrderedConstantModel):
    """Company employee range."""

    pass


class TurnoverRange(BaseOrderedConstantModel):
    """Company turnover range."""

    pass


class UKRegion(BaseConstantModel):
    """UK region."""

    pass


class Country(BaseConstantModel):
    """Country."""

    class Meta(BaseConstantModel.Meta):
        verbose_name_plural = 'countries'


class Title(BaseConstantModel):
    """Contact title."""

    pass


class Role(BaseConstantModel):
    """Contact role."""

    pass


class TeamRole(BaseConstantModel):
    """Team role."""
    team_role_groups = models.ManyToManyField(
        Group,
        verbose_name=_('Team role permission groups'),
        blank=True,
        help_text=_('Permission groups associated with this team.'),
        related_name="teamrole_set",
        related_query_name="team_role",
    )


class Team(BaseConstantModel):
    """Team."""

    role = models.ForeignKey(
        TeamRole,
        null=True, blank=True,
        related_name="%(class)ss",  # noqa: Q000
        on_delete=models.PROTECT,
    )
    uk_region = models.ForeignKey(
        UKRegion,
        null=True, blank=True,
        related_name="%(class)ss",  # noqa: Q000
        on_delete=models.PROTECT,
    )
    country = models.ForeignKey(
        Country,
        null=True, blank=True,
        related_name="%(class)ss",  # noqa: Q000
        on_delete=models.PROTECT,
    )


class Service(BaseConstantModel):
    """Service."""

    pass


class HeadquarterType(BaseConstantModel):
    """Head Quarter."""

    pass


class CompanyClassification(BaseConstantModel):
    """Company classification."""

    pass


class InvestmentProjectStage(BaseOrderedConstantModel):
    """Investment project stage."""


class InvestmentType(BaseConstantModel):
    """Investment type (for investment projects)."""


class FDIType(BaseConstantModel):
    """Investment type for foreign direct investments (for investment projects)."""


class NonFDIType(BaseConstantModel):
    """Investment type for non-foreign direct investments (for investment projects)."""


class ReferralSourceActivity(BaseConstantModel):
    """Referral source activity type (for investment projects)."""

    class Meta(BaseConstantModel.Meta):
        verbose_name_plural = 'referral source activities'


class ReferralSourceWebsite(BaseConstantModel):
    """Referral source website (for investment projects)."""


class ReferralSourceMarketing(BaseConstantModel):
    """Referral source – marketing activities (for investment projects)."""


class InvestmentBusinessActivity(BaseConstantModel):
    """Business activity (for investment projects)."""

    class Meta(BaseConstantModel.Meta):
        verbose_name_plural = 'investment business activities'


class InvestmentStrategicDriver(BaseConstantModel):
    """Strategic driver (for investment projects)."""


class SalaryRange(BaseOrderedConstantModel):
    """Salary ranges (used for investment projects)."""


class FDIValue(BaseOrderedConstantModel):
    """FDI value category (used for investment projects)."""
