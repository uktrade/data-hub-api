from datahub.metadata import models
from datahub.metadata.filters import ServiceFilterSet
from datahub.metadata.registry import registry
from datahub.metadata.serializers import (
    AdministrativeAreaSerializer,
    CountrySerializer,
    InvestmentProjectStageSerializer,
    SectorSerializer,
    ServiceSerializer,
    TeamSerializer,
)

registry.register(
    metadata_id='administrative-area',
    model=models.AdministrativeArea,
    queryset=models.AdministrativeArea.objects.select_related(
        'country',
    ),
    serializer=AdministrativeAreaSerializer,
)
registry.register(metadata_id='business-type', model=models.BusinessType)
registry.register(
    metadata_id='country',
    model=models.Country,
    queryset=models.Country.objects.select_related(
        'overseas_region',
    ),
    serializer=CountrySerializer,
)
registry.register(metadata_id='employee-range', model=models.EmployeeRange)
registry.register(metadata_id='overseas-region', model=models.OverseasRegion)
registry.register(
    filterset_fields={
        'level': ['lte'],
    },
    metadata_id='sector',
    model=models.Sector,
    queryset=models.Sector.objects.select_related(
        'parent',
        'parent__parent',
    ),
    serializer=SectorSerializer,
)

registry.register(
    filterset_class=ServiceFilterSet,
    metadata_id='service',
    model=models.Service,
    queryset=models.Service.objects.prefetch_related(
        'interaction_questions__answer_options',
    ).select_related(
        'parent',
    ).filter(
        children__isnull=True,
    ).order_by(
        'order',
    ),
    serializer=ServiceSerializer,
)
registry.register(metadata_id='team-role', model=models.TeamRole)
registry.register(
    metadata_id='team',
    model=models.Team,
    queryset=models.Team.objects.select_related('role', 'uk_region', 'country'),
    serializer=TeamSerializer,
)
registry.register(metadata_id='title', model=models.Title)
registry.register(metadata_id='turnover', model=models.TurnoverRange)
registry.register(metadata_id='uk-region', model=models.UKRegion)
registry.register(metadata_id='headquarter-type', model=models.HeadquarterType)
registry.register(metadata_id='investment-type', model=models.InvestmentType)
registry.register(metadata_id='fdi-type', model=models.FDIType)
registry.register(metadata_id='referral-source-activity', model=models.ReferralSourceActivity)
registry.register(metadata_id='referral-source-website', model=models.ReferralSourceWebsite)
registry.register(metadata_id='referral-source-marketing', model=models.ReferralSourceMarketing)
registry.register(
    metadata_id='investment-business-activity',
    model=models.InvestmentBusinessActivity,
)
registry.register(
    metadata_id='investment-strategic-driver',
    model=models.InvestmentStrategicDriver,
)
registry.register(metadata_id='salary-range', model=models.SalaryRange)
registry.register(
    metadata_id='investment-project-stage',
    model=models.InvestmentProjectStage,
    serializer=InvestmentProjectStageSerializer,
)
registry.register(metadata_id='fdi-value', model=models.FDIValue)
