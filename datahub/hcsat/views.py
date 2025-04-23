from rest_framework.permissions import IsAuthenticated

from datahub.core.viewsets import CoreViewSet
from datahub.hcsat.models import CustomerSatisfactionToolFeedback
from datahub.hcsat.serializers import CustomerSatisfactionToolFeedbackSerializer


class CustomerSatisfactionToolFeedbackViewSet(CoreViewSet):
    """Views for creating anonymous feedback (POST) and adding context (PATCH)."""

    serializer_class = CustomerSatisfactionToolFeedbackSerializer

    permission_classes = (IsAuthenticated,)

    queryset = CustomerSatisfactionToolFeedback.objects.all()
    lookup_field = 'pk'

    http_method_names = ['post', 'patch', 'head', 'options']
