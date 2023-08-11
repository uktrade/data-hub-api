import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.company.models import Company, CompanyPermission
from datahub.company.serializers import CompanySerializer
from datahub.core import statsd
from datahub.core.exceptions import (
    APIBadRequestException,
    APIUpstreamException,
)
from datahub.core.permissions import HasPermissions
from datahub.core.view_utils import enforce_request_content_type

from datahub.dnb_api.link_company import CompanyAlreadyDNBLinkedError, link_company_with_dnb
from datahub.dnb_api.models import HierarchyData
from datahub.dnb_api.queryset import get_company_queryset
from datahub.dnb_api.serializers import (
    DNBCompanyChangeRequestSerializer,
    DNBCompanyInvestigationSerializer,
    DNBCompanyLinkSerializer,
    DNBCompanySerializer,
    DNBGetCompanyChangeRequestSerializer,
    DNBMatchedCompanySerializer,
    DUNSNumberSerializer,
    SubsidiarySerializer,
)
from datahub.dnb_api.utils import (
    create_company_tree,
    create_investigation,
    DNBServiceConnectionError,
    DNBServiceError,
    DNBServiceInvalidRequestError,
    DNBServiceInvalidResponseError,
    DNBServiceTimeoutError,
    get_change_request,
    get_company,
    get_company_hierarchy_count,
    get_company_hierarchy_data,
    get_datahub_ids_for_dnb_service_company_hierarchy,
    get_reduced_company_hierarchy_data,
    request_changes,
    search_dnb,
    validate_company_id,
)


logger = logging.getLogger(__name__)


class DNBCompanySearchView(APIView):
    """
    View for searching DNB companies.
    """

    permission_classes = (
        HasPermissions(
            f'company.{CompanyPermission.view_company}',
        ),
    )

    @method_decorator(enforce_request_content_type('application/json'))
    def post(self, request):
        """
        Proxy to DNB search API for POST requests.  This will also hydrate results
        with Data Hub company details if the company exists (and can be matched)
        on Data Hub.
        """
        try:
            upstream_response = search_dnb(
                query_params=request.data,
                request=request,
            )

            response_body = upstream_response.json()
            response_body['results'] = self._format_and_hydrate(
                response_body.get('results', []),
            )
            return JsonResponse(response_body)
        except (
            DNBServiceConnectionError,
            DNBServiceTimeoutError,
        ) as exc:
            raise APIUpstreamException(str(exc))
        except DNBServiceError as exc:
            return HttpResponse(
                exc.message,
                status=exc.status_code,
                content_type='application/json',
            )

    def _get_datahub_companies_by_duns(self, duns_numbers):
        datahub_companies = get_company_queryset().filter(duns_number__in=duns_numbers)
        return {company.duns_number: company for company in datahub_companies}

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
            )
            for dnb_company in dnb_results
        )
        return [
            {
                'dnb_company': dnb_company,
                'datahub_company': datahub_company,
            }
            for dnb_company, datahub_company in dnb_datahub_company_pairs
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

    permission_classes = (
        HasPermissions(
            f'company.{CompanyPermission.view_company}',
            f'company.{CompanyPermission.add_company}',
        ),
    )

    def post(self, request):
        """
        Given a duns_number, get the data for the company from dnb-service
        and create a record in DataHub.
        """
        duns_serializer = DUNSNumberSerializer(data=request.data)
        duns_serializer.is_valid(raise_exception=True)
        duns_number = duns_serializer.validated_data['duns_number']

        try:
            dnb_company = get_company(duns_number, request)

        except (
            DNBServiceConnectionError,
            DNBServiceError,
            DNBServiceInvalidResponseError,
        ) as exc:
            raise APIUpstreamException(str(exc))

        except DNBServiceInvalidRequestError as exc:
            raise APIBadRequestException(str(exc))

        company_serializer = DNBCompanySerializer(
            data=dnb_company,
        )

        try:
            company_serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            message = 'Company data from DNB failed DH serializer validation'
            extra_data = {
                'formatted_dnb_company_data': dnb_company,
                'dh_company_serializer_errors': company_serializer.errors,
            }
            logger.error(message, extra=extra_data)
            raise

        datahub_company = company_serializer.save(
            created_by=request.user,
            modified_by=request.user,
            dnb_modified_on=now(),
        )

        statsd.incr('dnb.create.company')
        return Response(
            company_serializer.to_representation(datahub_company),
        )


class DNBCompanyLinkView(APIView):
    """
    View for linking a company to a DNB record.
    """

    permission_classes = (
        HasPermissions(
            f'company.{CompanyPermission.view_company}',
            f'company.{CompanyPermission.change_company}',
        ),
    )

    @method_decorator(enforce_request_content_type('application/json'))
    def post(self, request):
        """
        Given a Data Hub Company ID and a duns-number, link the Data Hub
        Company to the D&B record.
        """
        link_serializer = DNBCompanyLinkSerializer(data=request.data)

        link_serializer.is_valid(raise_exception=True)

        # This bit: validated_data['company_id'].id is weird but the alternative
        # is to rename the field to `company_id` which would (1) still be weird
        # and (2) leak the weirdness to the API
        company_id = link_serializer.validated_data['company_id'].id
        duns_number = link_serializer.validated_data['duns_number']

        try:
            company = link_company_with_dnb(company_id, duns_number, request.user)

        except (
            DNBServiceConnectionError,
            DNBServiceInvalidResponseError,
            DNBServiceError,
        ) as exc:
            raise APIUpstreamException(str(exc))

        except (
            DNBServiceInvalidRequestError,
            CompanyAlreadyDNBLinkedError,
        ) as exc:
            raise APIBadRequestException(str(exc))

        return Response(
            CompanySerializer().to_representation(company),
        )


class DNBCompanyChangeRequestView(APIView):
    """
    View for requesting change/s to DNB companies.
    """

    permission_classes = (
        HasPermissions(
            f'company.{CompanyPermission.view_company}',
            f'company.{CompanyPermission.change_company}',
        ),
    )

    @method_decorator(enforce_request_content_type('application/json'))
    def post(self, request):
        """
        A thin wrapper around the dnb-service change request API.
        """
        change_request_serializer = DNBCompanyChangeRequestSerializer(data=request.data)
        change_request_serializer.is_valid(raise_exception=True)

        try:
            response = request_changes(**change_request_serializer.validated_data)

        except (
            DNBServiceConnectionError,
            DNBServiceTimeoutError,
            DNBServiceError,
        ) as exc:
            raise APIUpstreamException(str(exc))

        return Response(response)

    def get(self, request):
        """
        A thin wrapper around the dnb-service change request API.
        """
        duns_number = request.query_params.get('duns_number', None)
        status = request.query_params.get('status', None)

        change_request_serializer = DNBGetCompanyChangeRequestSerializer(
            data={'duns_number': duns_number, 'status': status},
        )

        change_request_serializer.is_valid(raise_exception=True)

        try:
            response = get_change_request(**change_request_serializer.validated_data)

        except (
            DNBServiceConnectionError,
            DNBServiceTimeoutError,
            DNBServiceError,
        ) as exc:
            raise APIUpstreamException(str(exc))

        return Response(response)


class DNBCompanyInvestigationView(APIView):
    """
    View for creating a new investigation to get D&B to investigate and create a company record.
    """

    permission_classes = (
        HasPermissions(
            f'company.{CompanyPermission.view_company}',
            f'company.{CompanyPermission.change_company}',
        ),
    )

    @method_decorator(enforce_request_content_type('application/json'))
    def post(self, request):
        """
        A wrapper around the investigation API endpoint for dnb-service.
        """
        investigation_serializer = DNBCompanyInvestigationSerializer(data=request.data)
        investigation_serializer.is_valid(raise_exception=True)

        data = {'company_details': investigation_serializer.validated_data}
        company = data['company_details'].pop('company')

        try:
            response = create_investigation(data)

        except (
            DNBServiceConnectionError,
            DNBServiceTimeoutError,
            DNBServiceError,
        ) as exc:
            raise APIUpstreamException(str(exc))

        company.dnb_investigation_id = response['id']
        company.pending_dnb_investigation = True
        company.save()

        return Response(response)


class DNBCompanyHierarchyView(APIView):
    permission_classes = (
        HasPermissions(
            f'company.{CompanyPermission.view_company}',
        ),
    )

    def get(self, request, company_id):
        """
        Given a Company Id, get the data for the company hierarchy from dnb-service.
        """
        duns_number = validate_company_id(company_id)

        try:
            companies_count = get_company_hierarchy_count(duns_number)
            hierarchy_data = self.get_data(duns_number, companies_count)
        except (
            DNBServiceConnectionError,
            DNBServiceTimeoutError,
            DNBServiceError,
            DNBServiceInvalidRequestError,
            DNBServiceInvalidResponseError,
        ) as exc:
            raise APIUpstreamException(str(exc))

        json_response = {
            'ultimate_global_company': {},
            'ultimate_global_companies_count': 0,
            'family_tree_companies_count': 0,
            'manually_verified_subsidiaries': self.get_manually_verified_subsidiaries(
                company_id,
            ),
            'reduced_tree': hierarchy_data.reduced,
        }
        if not hierarchy_data.data:
            return Response(json_response)

        nested_tree = create_company_tree(hierarchy_data.data, duns_number)

        json_response['ultimate_global_company'] = nested_tree
        json_response['ultimate_global_companies_count'] = companies_count + 1
        json_response['family_tree_companies_count'] = hierarchy_data.count

        return Response(json_response)

    def get_data(self, duns_number, companies_count) -> HierarchyData:
        return None

    def get_manually_verified_subsidiaries(self, company_id):
        companies = Company.objects.filter(global_headquarters_id=company_id).select_related(
            'employee_range',
            'headquarter_type',
            'uk_region',
        )

        serialized_data = SubsidiarySerializer(companies, many=True)

        return serialized_data.data if companies else []


class DNBCompanyHierarchyReducedView(DNBCompanyHierarchyView):
    """
    View for receiving a reduced datahub hierarchy consisting of only immediate parents of
    a company from DNB data.
    """

    def get_data(self, duns_number, companies_count):
        return get_reduced_company_hierarchy_data(duns_number)


class DNBCompanyHierarchyFullView(DNBCompanyHierarchyView):
    """
    View for receiving datahub hierarchy of a company from DNB data.
    """

    def get_data(self, duns_number, companies_count):
        return get_company_hierarchy_data(duns_number)


class DNBRelatedCompaniesView(APIView):
    """
    View for receiving datahub hierarchy of a company from DNB data and return Data Hub IDs.
    """

    permission_classes = (
        HasPermissions(
            f'company.{CompanyPermission.view_company}',
            f'company.{CompanyPermission.add_company}',
        ),
    )

    def get(self, request, company_id):
        """
        Given a Company Id, get the data for the company hierarchy from dnb-service
        then find the related companies to create a list of IDs
        """
        company_ids = get_datahub_ids_for_dnb_service_company_hierarchy(
            include_parent_companies=(
                request.query_params.get('include_parent_companies') == 'true'
            ),
            include_subsidiary_companies=(
                request.query_params.get('include_subsidiary_companies') == 'true'
            ),
            company_id=company_id,
        )

        return Response(company_ids)


class DNBRelatedCompaniesCountView(APIView):
    """
    View for returning the count of related companies a company has
    """

    permission_classes = (
        HasPermissions(
            f'company.{CompanyPermission.view_company}',
        ),
    )

    def get(self, request, company_id):
        duns_number = validate_company_id(company_id)
        try:
            companies_count = get_company_hierarchy_count(duns_number)
        except (
            DNBServiceConnectionError,
            DNBServiceTimeoutError,
            DNBServiceError,
        ) as exc:
            raise APIUpstreamException(str(exc))

        json_response = {
            'related_companies_count': companies_count,
            'manually_linked_subsidiaries_count': 0,
            'total': companies_count,
            'reduced_tree': companies_count > settings.DNB_MAX_COMPANIES_IN_TREE_COUNT,
        }

        if request.query_params.get('include_manually_linked_companies') == 'true':
            subsidiary_companies_count = Company.objects.filter(
                global_headquarters_id=company_id,
            ).count()
            json_response['manually_linked_subsidiaries_count'] = subsidiary_companies_count
            json_response['total'] = companies_count + subsidiary_companies_count

        return Response(json_response)
