from datahub.core.viewsets import CoreViewSetV3
from datahub.investment.models import InvestmentProject
from datahub.investment.serializers import (
    InvestmentProjectSerializer, InvestmentProjectValueSerializer
)


class InvestmentProjectViewSet(CoreViewSetV3):
    read_serializer_class = InvestmentProjectSerializer
    write_serializer_class = InvestmentProjectSerializer
    queryset = InvestmentProject.objects.all()


class InvestmentProjectValueViewSet(CoreViewSetV3):
    read_serializer_class = InvestmentProjectValueSerializer
    write_serializer_class = InvestmentProjectValueSerializer
    queryset = InvestmentProject.objects.all()
