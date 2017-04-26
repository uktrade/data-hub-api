from datahub.core.viewsets import CoreViewSetV3
from datahub.investment.models import InvestmentProject
from datahub.investment.serializers import (
    IProjectSerializer, IProjectValueSerializer, IProjectRequirementsSerializer
)


class IProjectViewSet(CoreViewSetV3):
    read_serializer_class = IProjectSerializer
    write_serializer_class = IProjectSerializer
    queryset = InvestmentProject.objects.all()


class IProjectValueViewSet(CoreViewSetV3):
    read_serializer_class = IProjectValueSerializer
    write_serializer_class = IProjectValueSerializer
    queryset = InvestmentProject.objects.all()


class IProjectRequirementsViewSet(CoreViewSetV3):
    read_serializer_class = IProjectRequirementsSerializer
    write_serializer_class = IProjectRequirementsSerializer
    queryset = InvestmentProject.objects.all()
