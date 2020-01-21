from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from model_utils import Choices
from mptt.models import MPTTModel, TreeForeignKey

from datahub.core.exceptions import DataHubException
from datahub.core.fields import MultipleChoiceField
from datahub.core.models import BaseConstantModel, BaseOrderedConstantModel, DisableableModel
from datahub.core.utils import join_truthy_strings


class _MPTTObjectName:
    """
    This adds a cached property "name" to the model that gets a full name
    of the object using parent.
    """

    PATH_SEPARATOR = ' : '

    @cached_property
    def name(self):
        """Full name of the object in the form of a path."""
        ancestors = self._get_ancestors_and_self_using_parent()
        return self.PATH_SEPARATOR.join(getattr(ancestor, 'segment', '') for ancestor in ancestors)

    def _get_ancestors_and_self_using_parent(self):
        ancestors = [self]
        obj = self
        while getattr(obj, 'parent', None):
            obj = obj.parent
            if obj in ancestors:
                raise DataHubException('Recursive hierarchy encountered.')
            ancestors.append(obj)
        return reversed(ancestors)


class BusinessType(BaseConstantModel):
    """Company business type."""


class SectorCluster(BaseConstantModel):
    """Sector cluster."""


class Sector(MPTTModel, _MPTTObjectName, DisableableModel):
    """Company sector."""

    id = models.UUIDField(primary_key=True, default=uuid4)
    segment = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    sector_cluster = models.ForeignKey(
        SectorCluster,
        null=True, blank=True,
        related_name='%(class)ss',
        on_delete=models.PROTECT,
    )
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.PROTECT,
    )

    def __str__(self):
        """Human-readable representation."""
        return join_truthy_strings(
            self.segment,
            '(disabled)' if self.disabled_on else None,
        )

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


class AdministrativeArea(BaseConstantModel):
    """
    States, provinces etc. within a country.

    This is used by Market Access (but is not currently used in Data Hub CRM).
    """

    country = models.ForeignKey(
        Country,
        related_name='administrative_areas',
        on_delete=models.CASCADE,
    )


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
    """
    Team.

    Additional indexes created via migrations:

        Name: metadata_team_upper_name_ed973c5a
        Definition: UPPER(name)
        Comments: For when filtering by name__iexact
    """

    class Tag(models.TextChoices):
        INVESTMENT_SERVICES_TEAM = ('investment_services_team', 'Investment Services Team')

    role = models.ForeignKey(
        TeamRole,
        null=True, blank=True,
        related_name='%(class)ss',
        on_delete=models.PROTECT,
    )
    uk_region = models.ForeignKey(
        UKRegion,
        null=True, blank=True,
        related_name='%(class)ss',
        on_delete=models.PROTECT,
    )
    country = models.ForeignKey(
        Country,
        null=True, blank=True,
        related_name='%(class)ss',
        on_delete=models.PROTECT,
    )
    tags = MultipleChoiceField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=Tag.choices,
        blank=True,
    )

    class Meta(BaseConstantModel.Meta):
        indexes = [
            GinIndex(fields=['tags']),
        ]


class Service(MPTTModel, _MPTTObjectName, BaseOrderedConstantModel):
    """
    Service.

    Services use a tree structure managed by `django-mptt` so that we can group services that
    are somewhat related and make it easier to find them.

    Only the leaf services can be assigned to Interactions or Events.

    The roles of a Service with children nodes are grouping and visual aid.

    Services can only be added via a Django migration. Services cannot be
    edited through Django admin to make management easier.

    To add a new Service, you can use `load_yaml_data_in_migration` function and provide a
    path to the YAML formatted file containing the description of a new service.
    If you want to modify an existing service, the same function can be used and the
    primary key of the described service must match the existing service.

    We don't support removal of services. To disable a service, you can use a
    migration and update its `disabled_on` column value.

    Service name is composed of `segment` column values of each Service (going up the tree through
    the `parent` column), separated by colons or just the segment value if
    Service has no parent.

    For example:

    <parent service segment> : <service segment>
    Enquiry or Referral Received : General Export Enquiry
    Export Win
    """

    CONTEXTS = Choices(
        # Services that can be attached to an event
        ('event', 'Event'),
        # For interactions added to a company that are about export
        ('export_interaction', 'Export interaction'),
        # For service deliveries added to a company that are about export
        ('export_service_delivery', 'Export service delivery'),
        # For interactions added to a company about investment (but not a
        # specific investment project)
        ('investment_interaction', 'Investment interaction'),
        # For interactions added to a particular investment project
        ('investment_project_interaction', 'Investment project interaction'),
        # For interactions added to a company that are about not about export or investment
        ('other_interaction', 'Other interaction'),
        # For service deliveries added to a company that are about not about export or investment
        ('other_service_delivery', 'Other service delivery'),

        # TODO: Deprecated contexts  – remove once the front end has been updated to use
        # other contexts
        ('interaction', 'Interaction (deprecated)'),
        ('service_delivery', 'Service delivery (deprecated)'),
    )

    segment = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)

    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.PROTECT,
    )

    contexts = MultipleChoiceField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=CONTEXTS,
        blank=True,
        help_text='Contexts are only valid on leaf nodes.',
    )

    class Meta(BaseOrderedConstantModel.Meta):
        indexes = [
            GinIndex(fields=['contexts']),
        ]
        ordering = ('lft', )

    class MPTTMeta:
        order_insertion_by = ('segment',)


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
