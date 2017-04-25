from datahub.core.viewsets import CoreViewSetV1
from datahub.investment.models import InvestmentProject
from datahub.investment.serializers import InvestmentProjectSerializer


class InvestmentProjectViewSet(CoreViewSetV1):
    read_serializer_class = InvestmentProjectSerializer
    write_serializer_class = InvestmentProjectSerializer
    queryset = InvestmentProject.objects.all()
