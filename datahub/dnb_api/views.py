import logging

import sentry_sdk
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from statsd.defaults.django import statsd

from datahub.company.models import CompanyPermission
from datahub.core.exceptions import APIBadRequestException, APIUpstreamException
from datahub.core.permissions import HasPermissions
from datahub.core.view_utils import enforce_request_content_type
from datahub.dnb_api.constants import FEATURE_FLAG_DNB_COMPANY_SEARCH
from datahub.dnb_api.queryset import get_company_queryset
from datahub.dnb_api.serializers import (
    DNBCompanyInvestigationSerializer,
    DNBCompanySerializer,
    DNBMatchedCompanySerializer,
    DUNSNumberSerializer,
)
from datahub.dnb_api.utils import format_dnb_company, format_dnb_company_investigation, search_dnb
from datahub.feature_flag.utils import feature_flagged_view
from datahub.oauth.scopes import Scope


logger = logging.getLogger(__name__)


class DNBCompanySearchView(APIView):
    """
    View for searching DNB companies.
    """

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        HasPermissions(
            f'company.{CompanyPermission.view_company}',
        ),
    )

    @method_decorator(feature_flagged_view(FEATURE_FLAG_DNB_COMPANY_SEARCH))
    @method_decorator(enforce_request_content_type('application/json'))
    def post(self, request):
        """
        Proxy to DNB search API for POST requests.  This will also hydrate results
        with Data Hub company details if the company exists (and can be matched)
        on Data Hub.
        """
        upstream_response = search_dnb(request.data)
        statsd.incr(f'dnb.search.{upstream_response.status_code}')

        if upstream_response.status_code == status.HTTP_200_OK:
            response_body = upstream_response.json()
            response_body['results'] = self._format_and_hydrate(
                response_body.get('results', []),
            )
            return JsonResponse(response_body)

        return HttpResponse(
            upstream_response.text,
            status=upstream_response.status_code,
            content_type=upstream_response.headers.get('content-type'),
        )

    def _get_datahub_companies_by_duns(self, duns_numbers):
        datahub_companies = get_company_queryset().filter(duns_number__in=duns_numbers)
        return {
            company.duns_number: company for company in datahub_companies
        }

    def _get_datahub_company_data(self, datahub_company):
        if datahub_company:
            return DNBMatchedCompanySerializer(
                datahub_company,
                context={'request': self.request},
            ).data
        return None

    def _get_hydrated_results(self, dnb_results, datahub_companies_by_duns):
        dnb_datahub_company_pairs = (
            (
                dnb_company,
                self._get_datahub_company_data(
                    datahub_companies_by_duns.get(dnb_company['duns_number']),
                ),
            ) for dnb_company in dnb_results
        )
        return [
            {
                'dnb_company': dnb_company,
                'datahub_company': datahub_company,
            } for dnb_company, datahub_company in dnb_datahub_company_pairs
        ]

    def _format_and_hydrate(self, dnb_results):
        """
        Format each result from DNB such that there is a "dnb_company" key and
        a "datahub_company" key.  The value for "datahub_company" represents
        the corresponding Company entry on Data Hub for the DNB result, if it
        exists.

        This changes a DNB result entry from:

        {
          "duns_number": "999999999",
          "primary_name": "My Company LTD",
          ...
        }

        To:

        {
          "dnb_company": {
            "duns_number": "999999999",
            "primary_name": "My Company LTD",
            ...
          },
          "datahub_company": {
            "id": "0f5216e0-849f-11e6-ae22-56b6b6499611",
            "latest_interaction": {
              "id": "e8c3534f-4f60-4c93-9880-09c22e4fc011",
              "created_on": "2018-04-08T14:00:00Z",
              "date": "2018-06-06",
              "subject": "Meeting with Joe Bloggs"
            }
          }
        }

        """
        duns_numbers = [result['duns_number'] for result in dnb_results]
        datahub_companies_by_duns = self._get_datahub_companies_by_duns(duns_numbers)
        hydrated_results = self._get_hydrated_results(dnb_results, datahub_companies_by_duns)
        return hydrated_results


class DNBCompanyCreateView(APIView):
    """
    View for creating datahub company from DNB data.
    """

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        HasPermissions(
            f'company.{CompanyPermission.view_company}',
            f'company.{CompanyPermission.add_company}',
        ),
    )

    @method_decorator(feature_flagged_view(FEATURE_FLAG_DNB_COMPANY_SEARCH))
    def post(self, request):
        """
        Given a duns_number, get the data for the company from dnb-service
        and create a record in DataHub.
        """
        duns_serializer = DUNSNumberSerializer(data=request.data)
        duns_serializer.is_valid(raise_exception=True)
        duns_number = duns_serializer.validated_data['duns_number']

        dnb_response = search_dnb({'duns_number': duns_number})
        statsd.incr(f'dnb.search.{dnb_response.status_code}')

        if dnb_response.status_code != status.HTTP_200_OK:
            error_message = f'DNB service returned: {dnb_response.status_code}'
            logger.error(error_message)
            raise APIUpstreamException(error_message)

        dnb_companies = dnb_response.json().get('results', [])

        if not dnb_companies:
            error_message = f'Cannot find a company with duns_number: {duns_number}'
            logger.error(error_message)
            raise APIBadRequestException(error_message)

        if len(dnb_companies) > 1:
            error_message = f'Multiple companies found with duns_number: {duns_number}'
            logger.error(error_message)
            raise APIUpstreamException(error_message)

        formatted_company_data = format_dnb_company(
            dnb_companies[0],
        )
        company_serializer = DNBCompanySerializer(
            data=formatted_company_data,
        )

        try:
            company_serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            with sentry_sdk.push_scope() as scope:
                scope.set_extra('formatted_dnb_company_data', formatted_company_data)
                scope.set_extra('dh_company_serializer_errors', company_serializer.errors)
                sentry_sdk.capture_message('Company data from DNB failed DH serializer validation')
            raise

        datahub_company = company_serializer.save(
            created_by=request.user,
            modified_by=request.user,
        )

        statsd.incr(f'dnb.create.company')
        return Response(
            company_serializer.to_representation(datahub_company),
        )


class DNBCompanyCreateInvestigationView(APIView):
    """
    View for creating a company for DNB to investigate.

    This view is not inheriting from CoreViewSet because
    `format_dnb_company_investigation` mutates `request.data`
    which when shoehorned into CoreViewSet does not result in
    less or more readable code.
    """

    required_scopes = (Scope.internal_front_end, )
    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        HasPermissions(
            f'company.{CompanyPermission.view_company}',
            f'company.{CompanyPermission.add_company}',
        ),
    )

    @method_decorator(feature_flagged_view(FEATURE_FLAG_DNB_COMPANY_SEARCH))
    def post(self, request):
        """
        Given a minimal set of fields that may be necessary for DNB investigation,
        create a Company record in DataHub.
        """
        company_serializer = DNBCompanyInvestigationSerializer(
            data=format_dnb_company_investigation(request.data),
        )
        company_serializer.is_valid(raise_exception=True)

        datahub_company = company_serializer.save(
            created_by=request.user,
            modified_by=request.user,
            pending_dnb_investigation=True,
        )

        statsd.incr(f'dnb.create.investigation')
        return Response(
            company_serializer.to_representation(datahub_company),
        )
