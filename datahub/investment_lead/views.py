import logging

from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from rest_framework import generics

from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.serializers import EYBLeadSerializer


logger = logging.getLogger(__name__)


class EYBLeadCreateView(generics.CreateAPIView):
    """
    View for creating EYB Lead from incoming EYB payloads
    """

    queryset = EYBLead.objects.all()

    def post(self, request):
        eyb_lead_serializer = EYBLeadSerializer(data=request.data)

        try:
            eyb_lead_serializer.is_valid(raise_exception=True)
        except ValidationError:
            message = 'EYB lead data from EYB failed DH serializer validation'
            extra_data = {
                'formatted_eyblead_data': eyb_lead_serializer.data,
                'dh_eyblead_serializer_errors': eyb_lead_serializer.errors,
            }
            logger.error(message, extra=extra_data)
            raise

        eyb_lead = eyb_lead_serializer.save()

        return Response(
            eyb_lead_serializer.to_representation(eyb_lead),
        )
