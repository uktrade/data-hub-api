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
    path = r'{0}/$'.format(name)
    urls_args.append(((path, fn), {'name': name}))
