from datahub.core.viewsets import CoreViewSetV3
from datahub.investment.models import InvestmentProject
from datahub.investment.serializers import (
    IProjectRequirementsSerializer, IProjectSerializer, IProjectTeamSerializer,
    IProjectValueSerializer
)


class IProjectViewSet(CoreViewSetV3):
    """Investment project views.

    This is a subset of the fields on an InvestmentProject object.
    """

    read_serializer_class = IProjectSerializer
    write_serializer_class = IProjectSerializer
    queryset = InvestmentProject.objects.all()


class IProjectValueViewSet(CoreViewSetV3):
    """Investment project value views.

    This is a subset of the fields on an InvestmentProject object.
    """

    read_serializer_class = IProjectValueSerializer
    write_serializer_class = IProjectValueSerializer
    queryset = InvestmentProject.objects.all()


class IProjectRequirementsViewSet(CoreViewSetV3):
    """Investment project requirements views.

    This is a subset of the fields on an InvestmentProject object.
    """

    read_serializer_class = IProjectRequirementsSerializer
    write_serializer_class = IProjectRequirementsSerializer
    queryset = InvestmentProject.objects.all()


class IProjectTeamViewSet(CoreViewSetV3):
    """Investment project team views.

    This is a subset of the fields on an InvestmentProject object.
    """

    read_serializer_class = IProjectTeamSerializer
    write_serializer_class = IProjectTeamSerializer
    queryset = InvestmentProject.objects.all()
