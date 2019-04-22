from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from datahub.company.models import Company
from datahub.dnb_match.serializers import (
    SelectMatchingCandidateSerializer,
    SelectNoMatchSerializer,
)
from datahub.dnb_match.utils import (
    _get_list_of_latest_match_candidates,
    resolve_dnb_country_to_dh_country_dict,
)
from datahub.oauth.scopes import Scope


class BaseMatchingInformationAPIView(GenericAPIView):
    """Base matching information APIView."""

    required_scopes = (Scope.internal_front_end,)

    queryset = Company.objects.select_related('dnbmatchingresult')

    lookup_url_kwarg = 'company_pk'

    def _get_matching_information(self):
        """Get matching candidates and current selection."""
        company = self.get_object()
        try:
            matching_result = company.dnbmatchingresult.data
        except ObjectDoesNotExist:
            matching_result = {}

        response = {
            'result': self._get_dnb_match_result(matching_result),
            'candidates': _get_list_of_latest_match_candidates(company.pk),
            'company': model_to_dict(company, fields=('id', 'name', 'trading_names')),
        }

        normalised_response = _replace_dnb_country_fields(response)

        return Response(data=normalised_response)

    @staticmethod
    def _get_dnb_match_result(data):
        """Gets relevant information from DnBMatchingResult data."""
        if not data:
            data = {}

        dnb_match_keys = ('dnb_match', 'no_match', 'matched_by', 'adviser')
        return {key: value for key, value in data.items() if key in dnb_match_keys}


class MatchingInformationAPIView(BaseMatchingInformationAPIView):
    """APIView for company matching candidates information."""

    def get(self, request, **kwargs):
        """Get matching information."""
        return self._get_matching_information()


class SelectMatchAPIView(BaseMatchingInformationAPIView):
    """APIView for selecting matching company."""

    def post(self, request, **kwargs):
        """Create match selection."""
        company = self.get_object()

        serializer = SelectMatchingCandidateSerializer(
            data=request.data,
            context={**self.get_serializer_context(), 'company': company},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return self._get_matching_information()


class SelectNoMatchAPIView(BaseMatchingInformationAPIView):
    """APIView for selecting no match."""

    def post(self, request, **kwargs):
        """Create no match."""
        company = self.get_object()

        serializer = SelectNoMatchSerializer(
            data=request.data,
            context={**self.get_serializer_context(), 'company': company},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return self._get_matching_information()


def _replace_dnb_country_fields(data):
    """Replace DnB country fields with Data Hub countries."""
    for country_key in ('global_ultimate_country', 'country'):
        try:
            country = data['result']['dnb_match'][country_key]
        except KeyError:
            continue

        if isinstance(country, str):
            dh_country = resolve_dnb_country_to_dh_country_dict(
                country,
            )
            data['result']['dnb_match'][country_key] = dh_country

    if 'candidates' in data:
        for candidate in data['candidates']:
            for country_key in ('global_ultimate_country', 'address_country'):
                country = candidate[country_key]
                if isinstance(country, str):
                    dh_country = resolve_dnb_country_to_dh_country_dict(
                        country,
                    )
                    candidate[country_key] = dh_country

    return data
