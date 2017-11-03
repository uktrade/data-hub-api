from django.contrib import auth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from datahub.company.serializers import AdviserSerializer
from datahub.core.permissions import serialize_permissions


@api_view()
@permission_classes([IsAuthenticated])
def who_am_i(request):
    """Return the current user. This view is behind a login."""
    serializer = AdviserSerializer(request.user)
    data = serializer.data

    permissions = set()
    for backend in auth.get_backends():
        try:
            permissions.update(backend.get_all_permissions(user_obj=request.user))
        except AttributeError:
            pass

    data['permissions'] = serialize_permissions(permissions)
    return Response(data=data)
