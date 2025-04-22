from rest_framework.permissions import AllowAny

from datahub.core.viewsets import CoreViewSet
from datahub.hcsat.models import CustomerSatisfactionToolFeedback
from datahub.hcsat.serializers import CustomerSatisfactionToolFeedbackSerializer


class CustomerSatisfactionToolFeedbackViewSet(CoreViewSet):
    """Views for creating anonymous feedback (POST) and adding context (PATCH)."""

    serializer_class = CustomerSatisfactionToolFeedbackSerializer

    permission_classes = (AllowAny,) # TODO IS THIS CORRECT???

    queryset = CustomerSatisfactionToolFeedback.objects.all()
    lookup_field = 'pk'

    http_method_names = ['post', 'patch', 'head', 'options']
