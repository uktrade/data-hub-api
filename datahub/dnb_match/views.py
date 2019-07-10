from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

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


class BaseMatchingInformationAPIView(APIView):
    """Base matching information APIView."""

    required_scopes = (Scope.internal_front_end,)

    queryset = Company.objects.select_related('dnbmatchingresult')

    def _get_company(self):
        obj = get_object_or_404(self.queryset, pk=self.kwargs['company_pk'])
        self.check_object_permissions(self.request, obj)

        return obj

    @classmethod
    def _get_matching_information(cls, company):
        """Get matching candidates and current selection."""
        try:
            matching_result = company.dnbmatchingresult.data
        except ObjectDoesNotExist:
            matching_result = {}

        response = {
            'result': cls._get_dnb_match_result(matching_result),
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
        company = self._get_company()

        return self._get_matching_information(company)


class SelectMatchAPIView(BaseMatchingInformationAPIView):
    """APIView for selecting matching company."""

    def post(self, request, **kwargs):
        """Create match selection."""
        company = self._get_company()

        serializer = SelectMatchingCandidateSerializer(
            data=request.data,
            context={'request': request, 'company': company},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        company.refresh_from_db()

        return self._get_matching_information(company)


class SelectNoMatchAPIView(BaseMatchingInformationAPIView):
    """APIView for selecting no match."""

    def post(self, request, **kwargs):
        """Create no match."""
        company = self._get_company()

        serializer = SelectNoMatchSerializer(
            data=request.data,
            context={'request': request, 'company': company},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        company.refresh_from_db()

        return self._get_matching_information(company)


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
