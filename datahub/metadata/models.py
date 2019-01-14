from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
from mptt.models import MPTTModel, TreeForeignKey

from datahub.core.exceptions import DataHubException
from datahub.core.fields import MultipleChoiceField
from datahub.core.models import BaseConstantModel, BaseOrderedConstantModel, DisableableModel
from datahub.core.utils import join_truthy_strings


class BusinessType(BaseConstantModel):
    """Company business type."""


class SectorCluster(BaseConstantModel):
    """Sector cluster."""


class Sector(MPTTModel, DisableableModel):
    """Company sector."""

    PATH_SEPARATOR = ' : '

    id = models.UUIDField(primary_key=True, default=uuid4)
    segment = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    sector_cluster = models.ForeignKey(
        SectorCluster,
        null=True, blank=True,
        related_name="%(class)ss",  # noqa: Q000
        on_delete=models.PROTECT,
    )
    parent = TreeForeignKey(
        'self', null=True, blank=True, related_name='children', db_index=True,
        on_delete=models.PROTECT,
    )

    def __str__(self):
        """Human-readable representation."""
        return join_truthy_strings(
            self.segment,
            '(disabled)' if self.disabled_on else None,
        )

    @cached_property
    def name(self):
        """
        Full name of the sector in the form of a path.

        self.get_ancestors() is not used as it's incompatible with pre-fetching.
        """
        ancestors = self._get_ancestors_using_parent(include_self=True)
        return self.PATH_SEPARATOR.join(ancestor.segment for ancestor in ancestors)

    def _get_ancestors_using_parent(self, include_self=False):
        ancestors = [self] if include_self else []
        obj = self
        while obj.parent:
            obj = obj.parent
            if obj in ancestors:
                raise DataHubException('Recursive sector hierarchy encountered.')
            ancestors.append(obj)
        return reversed(ancestors)

    class MPTTMeta:
        order_insertion_by = ('segment',)


class EmployeeRange(BaseOrderedConstantModel):
    """Company employee range."""


class TurnoverRange(BaseOrderedConstantModel):
    """Company turnover range."""


class UKRegion(BaseConstantModel):
    """UK region."""


class OverseasRegion(BaseConstantModel):
    """DIT regions for overseas countries."""


class Country(BaseConstantModel):
    """Country."""

    overseas_region = models.ForeignKey(
        OverseasRegion,
        null=True,
        blank=True,
        related_name='countries',
        on_delete=models.PROTECT,
    )
    iso_alpha2_code = models.CharField(blank=True, max_length=2)

    class Meta(BaseConstantModel.Meta):
        verbose_name_plural = 'countries'


class Title(BaseConstantModel):
    """Contact title."""


class TeamRole(BaseConstantModel):
    """Team role."""

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('team role permission groups'),
        blank=True,
        help_text=_('Permission groups associated with this team.'),
        related_name='team_roles',
        related_query_name='team_roles',
    )


class Team(BaseConstantModel):
    """Team."""

    TAGS = Choices(
        ('investment_services_team', 'Investment Services Team'),
    )

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
    tags = MultipleChoiceField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=TAGS,
        blank=True,
    )

    class Meta(BaseConstantModel.Meta):
        indexes = [
            GinIndex(fields=['tags']),
        ]


class Service(BaseConstantModel):
    """Service."""

    CONTEXTS = Choices(
        ('event', 'Event'),
        ('interaction', 'Interaction'),
        ('investment_project_interaction', 'Investment project interaction'),
        ('service_delivery', 'Service delivery'),
    )

    contexts = MultipleChoiceField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=CONTEXTS,
        blank=True,
    )

    class Meta(BaseConstantModel.Meta):
        indexes = [
            GinIndex(fields=['contexts']),
        ]


class HeadquarterType(BaseOrderedConstantModel):
    """Headquarter type."""


class InvestmentProjectStage(BaseOrderedConstantModel):
    """Investment project stage."""

    exclude_from_investment_flow = models.BooleanField(
        help_text=_('If set to True the stage will not be part of the '
                    'linear flow and will be skipped.'),
        default=False,
    )


class InvestmentType(BaseConstantModel):
    """Investment type (for investment projects)."""


class FDIType(BaseConstantModel):
    """Investment type for foreign direct investments (for investment projects)."""


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
