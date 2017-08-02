from collections import namedtuple
from functools import partial

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from datahub.core.serializers import ConstantModelSerializer
from . import models
from .serializers import TeamSerializer

MetadataMapping = namedtuple('MetadataMapping', ['model', 'queryset', 'serializer'])


def build_mapping(model, queryset=None, serializer=ConstantModelSerializer):
    """Returns a MetadataMapping and defines defaults."""
    queryset = queryset if queryset is not None else model.objects.all()
    return MetadataMapping(model, queryset, serializer)


METADATA_MAPPING = {
    'business-type': build_mapping(models.BusinessType),
    'country': build_mapping(models.Country),
    'employee-range': build_mapping(models.EmployeeRange),
    'interaction-type': build_mapping(models.InteractionType),
    'role': build_mapping(models.Role),
    'sector': build_mapping(models.Sector),
    'service': build_mapping(models.Service),
    'team-role': build_mapping(models.TeamRole),
    'team': build_mapping(
        model=models.Team,
        queryset=models.Team.objects.select_related('role', 'uk_region', 'country'),
        serializer=TeamSerializer
    ),
    'title': build_mapping(models.Title),
    'turnover': build_mapping(models.TurnoverRange),
    'uk-region': build_mapping(models.UKRegion),
    'service-delivery-status': build_mapping(models.ServiceDeliveryStatus),
    'event': build_mapping(models.Event),
    'headquarter-type': build_mapping(models.HeadquarterType),
    'company-classification': build_mapping(models.CompanyClassification),
    'investment-type': build_mapping(models.InvestmentType),
    'fdi-type': build_mapping(models.FDIType),
    'non-fdi-type': build_mapping(models.NonFDIType),
    'referral-source-activity': build_mapping(models.ReferralSourceActivity),
    'referral-source-website': build_mapping(models.ReferralSourceWebsite),
    'referral-source-marketing': build_mapping(models.ReferralSourceMarketing),
    'investment-business-activity': build_mapping(models.InvestmentBusinessActivity),
    'investment-strategic-driver': build_mapping(models.InvestmentStrategicDriver),
    'salary-range': build_mapping(models.SalaryRange),
    'investment-project-stage': build_mapping(models.InvestmentProjectStage),
    'fdi-value': build_mapping(models.FDIValue),
}


@api_view()
@authentication_classes([])
@permission_classes([])
def metadata_view(request, mapping):
    """Metadata generic view."""
    serializer = mapping.serializer(mapping.queryset.all(), many=True)
    return Response(data=serializer.data)


urls_args = []

# programmatically generate metadata views
for name, mapping in METADATA_MAPPING.items():
    fn = partial(metadata_view, mapping=mapping)
    path = fr'^{name}/$'
    urls_args.append(((path, fn), {'name': name}))
