from rest_framework.generics import RetrieveAPIView

from datahub.company_activity.models.stova_event import StovaEvent
from datahub.company_activity.serializers.stova import StovaEventSerializer


class StovaEventRetrieveAPIView(RetrieveAPIView):
    queryset = StovaEvent.objects.all()
    serializer_class = StovaEventSerializer
