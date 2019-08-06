from urllib.parse import urljoin

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework import status
from rest_framework.views import APIView

from datahub.company.models import CompanyPermission
from datahub.core.api_client import APIClient, TokenAuth
from datahub.core.permissions import HasPermissions
from datahub.core.view_utils import enforce_request_content_type
from datahub.dnb_api.constants import FEATURE_FLAG_DNB_COMPANY_SEARCH
from datahub.dnb_api.queryset import get_company_queryset
from datahub.dnb_api.serializers import DNBMatchedCompanySerializer
from datahub.feature_flag.utils import feature_flagged_view
from datahub.oauth.scopes import Scope


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
        upstream_response = self._get_upstream_response(request)

        if upstream_response.status_code == status.HTTP_200_OK:
            response_body = upstream_response.json()
            response_body['results'] = self._format_and_hydrate(response_body['results'])
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
        else:
            return None

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

        hydrated_results = []

        for dnb_result in dnb_results:
            duns_number = dnb_result['duns_number']
            datahub_company = datahub_companies_by_duns.get(duns_number)
            datahub_company_data = self._get_datahub_company_data(datahub_company)
            hydrated_result = {'dnb_company': dnb_result, 'datahub_company': datahub_company_data}
            hydrated_results.append(hydrated_result)

        return hydrated_results

    def _get_upstream_response(self, request):

        if not settings.DNB_SERVICE_BASE_URL:
            raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')
        search_endpoint = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'companies/search/')
        shared_key_auth = TokenAuth(settings.DNB_SERVICE_TOKEN)
        api_client = APIClient(
            search_endpoint,
            shared_key_auth,
            raise_for_status=False,
        )
        return api_client.request(
            request.method,
            '',
            data=request.body,
            headers={
                'Content-Type': request.content_type,
            },
        )
