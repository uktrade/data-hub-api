from rest_framework import mixins, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Advisor
from .serializers import AdvisorSerializer, UserSerializer


class AdvisorReadOnlyViewSet(mixins.ListModelMixin,
                             mixins.RetrieveModelMixin,
                             viewsets.GenericViewSet):
    """Advisor GET only views."""

    serializer_class = AdvisorSerializer
    queryset = Advisor.objects.exclude(first_name='Undefined')


@api_view()
def who_am_i(request):
    """Return the current user. This view is behind a login."""

    serializer = UserSerializer(request.user)
    return Response(data=serializer.data)
