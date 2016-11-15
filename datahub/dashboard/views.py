from datetime import timedelta

from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.company.models import Contact, Interaction

from .serializers import IntelligentHomepageSerializer


class IntelligentHomepageView(APIView):
    """Return the data for the intelligent homepage."""

    http_method_names = ['get']

    def get(self, request, format=None):
        user = request.user
        days_in_the_past = now()-timedelta(days=15)

        interactions = Interaction.objects.filter(
            dit_advisor=user.advisor,
            created_on__gte=days_in_the_past
        ).order_by('-created_on')
        contacts = Contact.objects.filter(
            company__account_manager=user.advisor,
            created_on__gte=days_in_the_past
        ).order_by('-created_on')

        serializer = IntelligentHomepageSerializer({'interactions': interactions, 'contacts': contacts})
        return Response(data=serializer.data)
