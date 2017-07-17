from functools import partial

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from datahub.core.serializers import ConstantModelSerializer
from . import models

METADATA_MAPPING = {
    'business-type': models.BusinessType,
    'country': models.Country,
    'employee-range': models.EmployeeRange,
    'interaction-type': models.InteractionType,
    'role': models.Role,
    'sector': models.Sector,
    'service': models.Service,
    'team': models.Team,
    'title': models.Title,
    'turnover': models.TurnoverRange,
    'uk-region': models.UKRegion,
    'service-delivery-status': models.ServiceDeliveryStatus,
    'event': models.Event,
    'headquarter-type': models.HeadquarterType,
    'company-classification': models.CompanyClassification,
    'investment-type': models.InvestmentType,
    'fdi-type': models.FDIType,
    'non-fdi-type': models.NonFDIType,
    'referral-source-activity': models.ReferralSourceActivity,
    'referral-source-website': models.ReferralSourceWebsite,
    'referral-source-marketing': models.ReferralSourceMarketing,
    'investment-business-activity': models.InvestmentBusinessActivity,
    'investment-strategic-driver': models.InvestmentStrategicDriver,
    'salary-range': models.SalaryRange,
    'investment-project-stage': models.InvestmentProjectStage,
}


@api_view()
@authentication_classes([])
@permission_classes([])
def metadata_view(request, model):
    """Metadata generic view."""
    serializer = ConstantModelSerializer(model.objects.all(), many=True)
    return Response(data=serializer.data)


urls_args = []

# programmatically generate metadata views
for name, model in METADATA_MAPPING.items():
    fn = partial(metadata_view, model=model)
    path = fr'^{name}/$'
    urls_args.append(((path, fn), {'name': name}))
