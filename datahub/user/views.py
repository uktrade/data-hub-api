from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from datahub.user.serializers import WhoAmISerializer


@api_view()
@transaction.non_atomic_requests
@permission_classes([IsAuthenticated])
def who_am_i(request):
    """
    Return the current user. This view is behind a login.

    As this endpoint does not directly modify the database, it is opted out of atomic requests
    so that it does not cause a transaction to be used for the lifetime of the request.

    This should also ensure that when OAuth2 token introspection causes an access token to be
    inserted into the database, it is visible to other requests as soon as possible.

    See also: `datahub.core.reversion.NonAtomicRevisionMiddleware`.
    """
    serializer = WhoAmISerializer(request.user)

    return Response(data=serializer.data)
