from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from datahub.core import reversion
from datahub.core.exceptions import DataHubError
from datahub.core.fields import MultipleChoiceField
from datahub.core.models import (
    BaseConstantModel,
    BaseModel,
    BaseOrderedConstantModel,
    DisableableModel,
)
from datahub.core.utils import join_truthy_strings

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class _MPTTObjectName:
    """Adds a cached property "name" to the model that gets a full name
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
                raise DataHubError('Recursive hierarchy encountered.')
            ancestors.append(obj)
        return reversed(ancestors)


class BusinessType(BaseConstantModel):
    """Company business type."""


class SectorCluster(BaseConstantModel):
    """Sector cluster."""


@reversion.register_base_model()
class Sector(MPTTModel, _MPTTObjectName, DisableableModel):
    """Company sector."""

    id = models.UUIDField(primary_key=True, default=uuid4)
    segment = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    sector_cluster = models.ForeignKey(
        SectorCluster,
        null=True,
        blank=True,
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
    export_win_id = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
    )

    def __str__(self):
        """Human-readable representation."""
        return join_truthy_strings(
            self.segment,
            '(disabled)' if self.disabled_on else None,
        )

    @staticmethod
    def get_name_from_segments(segments: list[str | None]) -> str:
        """Gets a sector's full name from a list of segments, some of which can be None."""
        name = ' : '.join([segment.strip() for segment in segments if segment not in [None, '']])
        return name

    @staticmethod
    def get_selected_and_parent_segments(name) -> tuple[str, str | None]:
        """Determines the selected and parent sector segments from the sector name."""
        if not isinstance(name, str):
            return None
        segments = name.split(':')
        selected_segment = segments[-1].strip()
        parent_segment = segments[-2].strip() if len(segments) > 1 else None
        return selected_segment, parent_segment

    @staticmethod
    def get_segments_from_sector_instance(sector) -> tuple[str, str | None, str | None]:
        """Splits a sector name into individual segments and returns a tuple of segments.

        If a sector is a level zero or one, the level one and two segments will
        be None where applicable.

        This function is tailored to a max of three levels.
        """
        segments = sector.name.split(' : ')
        return tuple(segments[i] if i < len(segments) else None for i in range(3))

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
    iso_alpha2_code = models.CharField(blank=True, max_length=5)

    # If True, country is included in Export Wins drop downs
    is_export_win = models.BooleanField(default=True)

    class Meta(BaseConstantModel.Meta):
        verbose_name_plural = 'countries'


class TradeAgreement(BaseConstantModel):
    """Trade agreements for events."""


class ExchangeRate(BaseModel):
    """Exchange rates."""

    id = models.UUIDField(primary_key=True, default=uuid4)
    from_currency_code = models.CharField(max_length=3)
    to_currency_code = models.CharField(max_length=3)
    exchange_rate = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['from_currency_code', 'to_currency_code'],
                name='unique_from_currency_code_to_currency_code',
            ),
        ]


class AdministrativeArea(BaseConstantModel):
    """States, provinces etc. within a country.

    This is used by Market Access (but is not currently used in Data Hub CRM).
    """

    country = models.ForeignKey(
        Country,
        related_name='administrative_areas',
        on_delete=models.CASCADE,
    )
    area_code = models.CharField(blank=True, max_length=3)
    area_name = models.CharField(blank=True, max_length=255)

    def __str__(self):
        """To make this clearer for anyone using the admin drop down on this data."""
        return f'{self.name} ({self.country.name})'


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
    """Team.

    Additional indexes created via migrations:

        Name: metadata_team_upper_name_ed973c5a
        Definition: UPPER(name)
        Comments: For when filtering by name__iexact
    """

    class Tag(models.TextChoices):
        INVESTMENT_SERVICES_TEAM = ('investment_services_team', 'Investment Services Team')

    role = models.ForeignKey(
        TeamRole,
        null=True,
        blank=True,
        related_name='%(class)ss',
        on_delete=models.PROTECT,
    )
    uk_region = models.ForeignKey(
        UKRegion,
        null=True,
        blank=True,
        related_name='%(class)ss',
        on_delete=models.PROTECT,
    )
    country = models.ForeignKey(
        Country,
        null=True,
        blank=True,
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
    """Service.

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

    class Context(models.TextChoices):
        # Services that can be attached to an event
        EVENT = ('event', 'Event')
        # For interactions added to a company that are about export
        EXPORT_INTERACTION = ('export_interaction', 'Export interaction')
        # For service deliveries added to a company that are about export
        EXPORT_SERVICE_DELIVERY = ('export_service_delivery', 'Export service delivery')
        # For interactions added to a company about investment (but not a
        # specific investment project)
        INVESTMENT_INTERACTION = ('investment_interaction', 'Investment interaction')
        # For interactions added to a particular investment project
        INVESTMENT_PROJECT_INTERACTION = (
            'investment_project_interaction',
            'Investment project interaction',
        )
        TRADE_AGREEMENT_INTERACTION = (
            'trade_agreement_interaction',
            'Trade agreement interaction',
        )
        # For interactions added to a company that are about not about export or investment
        OTHER_INTERACTION = ('other_interaction', 'Other interaction')
        # For service deliveries added to a company that are about not about export or investment
        OTHER_SERVICE_DELIVERY = ('other_service_delivery', 'Other service delivery')

        # TODO: Deprecated contexts  – remove once the front end has been updated to use
        # other contexts
        INTERACTION = ('interaction', 'Interaction (deprecated)')
        SERVICE_DELIVERY = ('service_delivery', 'Service delivery (deprecated)')

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
        choices=Context.choices,
        blank=True,
        help_text='Contexts are only valid on leaf nodes.',
    )

    class Meta(BaseOrderedConstantModel.Meta):
        indexes = [
            GinIndex(fields=['contexts']),
        ]
        ordering = ('lft',)

    class MPTTMeta:
        order_insertion_by = ('segment',)


class HeadquarterType(BaseOrderedConstantModel):
    """Headquarter type."""


class InvestmentProjectStage(BaseOrderedConstantModel):
    """Investment project stage."""

    exclude_from_investment_flow = models.BooleanField(
        help_text=_(
            'If set to True the stage will not be part of the linear flow and will be skipped.',
        ),
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
    """Referral source - marketing activities (for investment projects)."""


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


class ExportBarrierType(BaseOrderedConstantModel):
    """Export barrier type (used for company interactions)."""


class PostcodeData(models.Model):  # noqa: DJ008
    """Model representing ONS Postcode Data (ONSPD).

    The ONSPD relates both current and terminated postcodes in the United Kingdom to a range
    of current statutory administrative, electoral, health and other area geographies.

    The ONSPD is issued quarterly. See
    https://geoportal.statistics.gov.uk/datasets/6fb8941d58e54d949f521c92dfb92f2a/about for
    more details.
    """

    id = models.IntegerField(
        primary_key=True,
        help_text='External ID from data workspace',
    )
    ccg = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Clinical Commissioning Group',
    )
    ced = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='County Electoral Division',
    )
    eer = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='European Electoral Region',
    )
    imd = models.IntegerField(
        null=True,
        help_text='Index of Multiple Deprivation',
    )
    lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text='Degress Latitude',
    )
    pcd = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Unit Postcode (7 character version)',
    )
    pct = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Primary Care Trust',
    )
    pfa = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Police Force Area',
    )
    rgn = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Region Code',
    )
    stp = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Sustainability and Transformation Partnership',
    )
    ctry = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Country',
    )
    lep1 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Primary Local Enterprise Partnership',
    )
    lep2 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Secondary Local Enterprise Partnership',
    )
    long = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text='Degrees Longitude',
    )
    nuts = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='International Terratorial Levels (ITL  - Former\
        Nomenclature of Units for Territorial Statistics (NUTS)',
    )
    oa01 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='2001 Census Output Area',
    )
    oa11 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='2011 Census Output Area/Small Area',
    )
    oa21 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='2021 Census Output Area',
    )
    park = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='National Parks',
    )
    pcd2 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Unit Postcode (8 character version)',
    )
    pcds = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Unit Postcode (variable length version)',
    )
    pcon = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Westminster Parliamentary Consituency',
    )
    ttwa = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Travel to Work Area',
    )
    wz11 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Workplace Zone',
    )
    bua11 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Built-up Area',
    )
    nhser = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='NHS England Region',
    )
    oac01 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Census Area Output Classification',
    )
    oac11 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Census Area/Small Area Output Classification',
    )
    oscty = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='County',
    )
    streg = models.IntegerField(
        null=True,
        help_text='Standard Statistical Region',
    )
    calncv = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Cancer Alliance',
    )
    dointr = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date of Introduction (YYYYMM)',
    )
    doterm = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date of Termination (YYYYMM)',
    )
    lsoa01 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='2001 Census Lower Layer Super Output Area',
    )
    lsoa11 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='2011 Census Lower Layer Super Output Area',
    )
    lsoa21 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='2021 Census Lower Layer Super Output Area',
    )
    msoa01 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='2001 Census Middle Layer Super Output Area',
    )
    msoa11 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='2011 Census Middle Layer Super Output Area',
    )
    msoa21 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='2021 Census Middle Layer Super Output Area',
    )
    oslaua = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Local Authority District',
    )
    osward = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Electoral Ward',
    )
    parish = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Parish',
    )
    teclec = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Local Learning and Skills Council',
    )
    buasd11 = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Built-up Areas Subdivision',
    )
    casward = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Census Area Statistics Ward',
    )
    ru11ind = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Census Rural-Urban Classification',
    )
    ur01ind = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Census Rural-Urban Indicator',
    )
    oseast1m = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='National Grid Reference - Easting',
    )
    osgrdind = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Grid Reference Positional Quality Indicator',
    )
    oshlthau = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Former Strategic Health Authority/Health Board',
    )
    osnrth1m = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='National Grid Reference - Northing',
    )
    usertype = models.IntegerField(
        null=True,
        help_text='Postcode User Type (0 - Small or 1 - Large)',
    )
    statsward = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Statistical Ward',
    )
    region_name = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Region Name',
    )
    pcd_normalised = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Unit Postcode Normalised',
    )
    uk_super_region = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='UK Super Region',
    )
    publication_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Publication Date',
    )
    local_authority_district_name = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text=' Local Authority District Name',
    )
    parliamentary_constituency_name = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Parliamentary Constituency Name',
    )
    lep1_local_enterprise_partnership_name = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Primary Local Enterprise Partnership Name',
    )
    lep2_local_enterprise_partnership_name = models.CharField(  # noqa: DJ001
        max_length=MAX_LENGTH,
        null=True,
        blank=True,
        help_text='Secondary Local Enterprise Partnership Name',
    )
