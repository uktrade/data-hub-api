from . import models
from .registry import registry
from .serializers import CountrySerializer, TeamSerializer

registry.register(metadata_id='business-type', model=models.BusinessType)
registry.register(
    metadata_id='country',
    model=models.Country,
    serializer=CountrySerializer
)
registry.register(metadata_id='employee-range', model=models.EmployeeRange)
registry.register(metadata_id='interaction-type', model=models.InteractionType)
registry.register(metadata_id='role', model=models.Role)
registry.register(metadata_id='sector', model=models.Sector)
registry.register(metadata_id='service', model=models.Service)
registry.register(metadata_id='team-role', model=models.TeamRole)
registry.register(
    metadata_id='team',
    model=models.Team,
    queryset=models.Team.objects.select_related('role', 'uk_region', 'country'),
    serializer=TeamSerializer
),
registry.register(metadata_id='title', model=models.Title)
registry.register(metadata_id='turnover', model=models.TurnoverRange)
registry.register(metadata_id='uk-region', model=models.UKRegion)
registry.register(metadata_id='service-delivery-status', model=models.ServiceDeliveryStatus)
registry.register(metadata_id='event', model=models.Event)
registry.register(metadata_id='headquarter-type', model=models.HeadquarterType)
registry.register(metadata_id='company-classification', model=models.CompanyClassification)
registry.register(metadata_id='investment-type', model=models.InvestmentType)
registry.register(metadata_id='fdi-type', model=models.FDIType)
registry.register(metadata_id='non-fdi-type', model=models.NonFDIType)
registry.register(metadata_id='referral-source-activity', model=models.ReferralSourceActivity)
registry.register(metadata_id='referral-source-website', model=models.ReferralSourceWebsite)
registry.register(metadata_id='referral-source-marketing', model=models.ReferralSourceMarketing)
registry.register(
    metadata_id='investment-business-activity',
    model=models.InvestmentBusinessActivity
)
registry.register(
    metadata_id='investment-strategic-driver',
    model=models.InvestmentStrategicDriver
)
registry.register(metadata_id='salary-range', model=models.SalaryRange)
registry.register(metadata_id='investment-project-stage', model=models.InvestmentProjectStage)
registry.register(metadata_id='fdi-value', model=models.FDIValue)
