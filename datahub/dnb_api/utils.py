import logging
import uuid


from datetime import timedelta
from itertools import islice

import numpy as np
import pandas as pd

import reversion

from bigtree import (
    dataframe_to_tree_by_relation,
    find,
    tree_to_nested_dict,
)

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.utils.timezone import now
from requests.exceptions import ConnectionError, Timeout
from rest_framework import serializers, status
from rest_framework.response import Response

from reversion.models import Version

from datahub.company.models import Company
from datahub.core import statsd
from datahub.core.api_client import APIClient, TokenAuth
from datahub.core.exceptions import (
    APIBadGatewayException,
    APIBadRequestException,
    APINotFoundException,
    APIUpstreamException,
)
from datahub.core.serializers import AddressSerializer
from datahub.dnb_api.constants import (
    ALL_DNB_UPDATED_MODEL_FIELDS,
    ALL_DNB_UPDATED_SERIALIZER_FIELDS,
    MAX_COMPANIES_IN_TREE_COUNT,
)
from datahub.dnb_api.models import HierarchyData
from datahub.dnb_api.serializers import DNBCompanyHierarchySerializer, DNBCompanySerializer
from datahub.metadata.models import AdministrativeArea, Country
from datahub.search.company.models import Company as SearchCompany
from datahub.search.execute_query import execute_search_query
from datahub.search.query_builder import get_search_by_entities_query

logger = logging.getLogger(__name__)
MAX_DUNS_NUMBERS_PER_REQUEST = 1024


class DNBServiceBaseError(Exception):
    """
    Base exception class for DNBService related errors.
    """


class DNBServiceError(DNBServiceBaseError):
    """
    Exception for when DNB service doesn't return a response with a status code of 200.
    """

    def __init__(self, message, status_code):
        """
        Initialise the exception.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DNBServiceInvalidRequestError(DNBServiceBaseError):
    """
    Exception for when the request to DNB service is not valid.
    """


class DNBServiceInvalidResponseError(DNBServiceBaseError):
    """
    Exception for when the response from DNB service is not valid.
    """


class DNBServiceConnectionError(DNBServiceBaseError):
    """
    Exception for when an error was encountered when connecting to DNB service.
    """


class DNBServiceTimeoutError(DNBServiceBaseError):
    """
    Exception for when a timeout was encountered when connecting to DNB service.
    """


class RevisionNotFoundError(Exception):
    """
    Exception for when a revision with the specified comment is not found.
    """


def search_dnb(query_params, request=None):
    """
    Queries the dnb-service with the given query_params. E.g.:

        {"duns_number": "29393217", "page_size": 1}
        {"search_term": "brompton", "page_size": 10}
    """
    if not settings.DNB_SERVICE_BASE_URL:
        raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')

    def api_request(api_client):
        return api_client.request(
            'POST',
            'v2/companies/search/',
            json=query_params,
            timeout=3.0,
        )

    response = call_api_request_with_exception_handling(api_request, 'dnb.search')

    return response


def get_dnb_company_data(duns_number, request=None):
    """
    Pull data for the company with the given duns_number from DNB and
    returns the raw data.

    Raises exceptions if the company is not found, if multiple companies are
    found or if the `duns_number` for the company is not the same as the one
    we searched for.
    """
    dnb_response = search_dnb({'duns_number': duns_number})

    dnb_companies = dnb_response.json().get('results', [])
    if not dnb_companies:
        error_message = f'Cannot find a company with duns_number: {duns_number}'
        logger.error(error_message)
        raise DNBServiceInvalidRequestError(error_message)

    if len(dnb_companies) > 1:
        error_message = f'Multiple companies found with duns_number: {duns_number}'
        logger.error(error_message)
        raise DNBServiceInvalidResponseError(error_message)

    dnb_company = dnb_companies[0]

    if dnb_company.get('duns_number') != duns_number:
        error_message = (
            f'DUNS number of the company: {dnb_company.get("duns_number")} '
            f'did not match searched DUNS number: {duns_number}'
        )
        logger.error(error_message)
        raise DNBServiceInvalidResponseError(error_message)

    return dnb_company


def get_company(duns_number, request=None):
    """
    Pull data for the company with the given duns_number from DNB and
    returns a dict formatted for use with serializer of type CompanySerializer.

    Raises exceptions if the company is not found, if multiple companies are
    found or if the `duns_number` for the company is not the same as the one
    we searched for.
    """
    return format_dnb_company(get_dnb_company_data(duns_number, request))


def extract_address_from_dnb_company(dnb_company, prefix, ignore_when_missing=()):
    """
    Extract address from dnb company data.  This takes a `prefix` string to
    extract address fields that start with a certain prefix.
    """
    country = (
        Country.objects.filter(
            iso_alpha2_code=dnb_company[f'{prefix}_country'],
        ).first()
        if dnb_company.get(f'{prefix}_country')
        else None
    )
    area = (
        AdministrativeArea.objects.filter(
            area_code=dnb_company[f'{prefix}_area_abbrev_name'],
        ).first()
        if dnb_company.get(f'{prefix}_area_abbrev_name')
        else None
    )

    extracted_address = {
        'line_1': dnb_company.get(f'{prefix}_line_1') or '',
        'line_2': dnb_company.get(f'{prefix}_line_2') or '',
        'town': dnb_company.get(f'{prefix}_town') or '',
        'county': dnb_company.get(f'{prefix}_county') or '',
        'postcode': dnb_company.get(f'{prefix}_postcode') or '',
        'country': country.id if country else None,
        'area': area.id if area else None,
    }

    for field in ignore_when_missing:
        if not extracted_address[field]:
            return None

    return extracted_address


def format_dnb_company(dnb_company):
    """
    Format DNB response to something that our Serializer
    can work with.
    """
    # Extract companies house number for UK Companies
    registration_numbers = {
        reg['registration_type']: reg.get('registration_number')
        for reg in dnb_company.get('registration_numbers') or []
    }

    domain = dnb_company.get('domain')
    company_website = f'http://{domain}' if domain else ''

    duns_number = dnb_company.get('duns_number')
    turnover_currency = dnb_company.get('annual_sales_currency')

    if turnover_currency and turnover_currency != 'USD':
        logger.error(
            'D&B did not have USD turnover',
            extra={
                'duns_number': duns_number,
                'currency': turnover_currency,
            },
        )
        dnb_company.pop('annual_sales', None)
        dnb_company.pop('is_annual_sales_estimated', None)

    return {
        'name': dnb_company.get('primary_name'),
        'trading_names': dnb_company.get('trading_names'),
        'duns_number': duns_number,
        'address': extract_address_from_dnb_company(dnb_company, 'address'),
        'registered_address': extract_address_from_dnb_company(
            dnb_company,
            'registered_address',
            ignore_when_missing=AddressSerializer.REQUIRED_FIELDS,
        ),
        'uk_based': dnb_company.get('address_country') == 'GB',
        'company_number': registration_numbers.get('uk_companies_house_number'),
        # Optional fields
        'number_of_employees': dnb_company.get('employee_number'),
        'is_number_of_employees_estimated': dnb_company.get(
            'is_employees_number_estimated',
        ),
        'turnover': dnb_company.get('annual_sales'),
        'is_turnover_estimated': dnb_company.get('is_annual_sales_estimated'),
        'website': company_website,
        # `Company.global_ultimate_duns_number` is not nullable but allows blank values. Sample
        # response from the D&B search API suggests that this field can be set to null.
        'global_ultimate_duns_number': dnb_company.get('global_ultimate_duns_number') or '',
        # TODO: Extract sensible values for the following fields form the data:
        # 'business_type': None,
        # 'description': None,
        # 'uk_region': None,
        # 'sector': None,
        # 'vat_number': None,
    }


def update_company_from_dnb(
    dh_company,
    dnb_company,
    user=None,
    fields_to_update=None,
    update_descriptor='',
):
    """
    Updates `dh_company` with new data from `dnb_company` while setting `modified_by` to the
    given user (if specified) and creating a revision.
    If `fields_to_update` is specified, only the fields specified will be synced
    with DNB.  `fields_to_update` should be an iterable of strings representing
    DNBCompanySerializer field names.
    If `update_descriptor` is specified, the descriptor will be injected in to
    the comment for this revision.

    Raises serializers.ValidationError if data is invalid.
    """
    fields_to_update = fields_to_update or ALL_DNB_UPDATED_SERIALIZER_FIELDS
    # Set dnb_company data to only include the fields in fields_to_update

    dnb_company = {field: dnb_company[field] for field in fields_to_update}

    company_serializer = DNBCompanySerializer(
        dh_company,
        data=dnb_company,
        partial=True,
    )

    try:
        company_serializer.is_valid(raise_exception=True)

    except serializers.ValidationError:
        logger.error(
            'Data from D&B did not pass the Data Hub validation checks.',
            extra={'dnb_company': dnb_company, 'errors': company_serializer.errors},
        )
        raise

    with reversion.create_revision():
        company_kwargs = {
            'pending_dnb_investigation': False,
            'dnb_modified_on': now(),
        }
        if user:
            company_kwargs['modified_by'] = user
            reversion.set_user(user)
            company_serializer.save(**company_kwargs)
        else:
            # Call a method to update the fields changed on the serializer only; this prevents
            # us from modifying modified_on - which should only be set through saves initiated by
            # a user
            company_serializer.partial_save(**company_kwargs)

        update_comment = 'Updated from D&B'
        if update_descriptor:
            update_comment = f'{update_comment} [{update_descriptor}]'
        reversion.set_comment(update_comment)


def get_company_update_page(last_updated_after, next_page=None, request=None):
    """
    Get the given company updates page from the dnb-service.

    The request to the dnb-service would look like:

        GET /companies?last_updated_after=2019-11-11T12:00:00&cursor=3465723323

    Where:

        last_updated_after: datetime filter that ensures that only companies
        updated after the given datetime are returned.

        cursor: dnb-service users DRF's CursorPagination for this paginated list
        and cursor is a encoded string that identifies a given page.
    """
    if not settings.DNB_SERVICE_BASE_URL:
        raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')

    request_kwargs = {'timeout': 3.0}
    url = next_page
    if not next_page:
        request_kwargs['params'] = {
            'last_updated_after': last_updated_after,
        }
        url = 'companies/'

    try:
        api_client = _get_api_client(request)
        response = api_client.request(
            'GET',
            url,
            **request_kwargs,
        )
    except APIBadGatewayException as exc:
        error_message = 'DNB service unavailable'
        logger.error(error_message)
        raise DNBServiceConnectionError(error_message) from exc
    except Timeout as exc:
        error_message = 'Encountered a timeout interacting with DNB service'
        logger.error(error_message)
        raise DNBServiceTimeoutError(error_message) from exc

    if response.status_code != status.HTTP_200_OK:
        error_message = f'DNB service returned an error status: {response.status_code}'
        logger.error(error_message)
        raise DNBServiceError(error_message, response.status_code)

    return response.json()


def _get_rollback_version(company, update_comment):
    versions = Version.objects.get_for_object(company)
    for i, version in enumerate(versions):
        if version.revision.comment == update_comment:
            if (i + 1) < len(versions):
                return versions[i + 1]
            raise RevisionNotFoundError(
                f'Revision with comment: {update_comment} is the base version.',
            )
    raise RevisionNotFoundError(
        f'Revision with comment: {update_comment} not found.',
    )


def rollback_dnb_company_update(
    company,
    update_descriptor,
    fields_to_update=None,
):
    """
    Given a company, an update descriptor that identifies a particular update
    patch and fields that default to ALL_DNB_UPDATE_FIELDS, rollback the record
    to the state before the update was applied.
    """
    fields_to_update = fields_to_update or ALL_DNB_UPDATED_MODEL_FIELDS
    update_comment = f'Updated from D&B [{update_descriptor}]'
    rollback_version = _get_rollback_version(company, update_comment)
    fields = {
        name: value
        for name, value in rollback_version.field_dict.items()
        if name in fields_to_update
    }
    with reversion.create_revision():
        reversion.set_comment(f'Reverted D&B update from: {update_descriptor}')
        for field, value in fields.items():
            setattr(company, field, value)
        company.save(update_fields=fields)


def _request_changes(payload, request=None):
    """
    Submit change request to dnb-service.
    """
    if not settings.DNB_SERVICE_BASE_URL:
        raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')

    api_client = _get_api_client(request)
    response = api_client.request(
        'POST',
        'change-request/',
        json=payload,
        timeout=3.0,
    )
    return response


def request_changes(duns_number, changes, request=None):
    """
    Submit change request for the company with the given duns_number
    and changes to the dnb-service.
    """
    try:
        dnb_response = _request_changes(
            {
                'duns_number': duns_number,
                'changes': changes,
            },
            request=request,
        )
    except APIBadGatewayException as exc:
        error_message = 'DNB service unavailable'
        raise DNBServiceConnectionError(error_message) from exc

    except Timeout as exc:
        error_message = 'Encountered a timeout interacting with DNB service'
        raise DNBServiceTimeoutError(error_message) from exc

    if not dnb_response.ok:
        error_message = f'DNB service returned an error status: {dnb_response.status_code}'
        raise DNBServiceError(error_message, dnb_response.status_code)

    return dnb_response.json()


def _get_change_request(params, request=None):
    """
    Get change request from dnb-service.
    """
    if not settings.DNB_SERVICE_BASE_URL:
        raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')
    api_client = _get_api_client(request)
    response = api_client.request(
        'GET',
        'change-request/',
        params=params,
        timeout=3.0,
    )
    return response


def get_change_request(duns_number, status, request=None):
    """
    Get a change request for the company with the given duns_number
    and status from the dnb-service.
    """
    try:
        dnb_response = _get_change_request(
            {
                'duns_number': duns_number,
                'status': status,
            },
            request,
        )

    except ConnectionError as exc:
        error_message = 'Encountered an error connecting to DNB service'
        raise DNBServiceConnectionError(error_message) from exc

    except Timeout as exc:
        error_message = 'Encountered a timeout interacting with DNB service'
        raise DNBServiceTimeoutError(error_message) from exc

    if not dnb_response.ok:
        error_message = f'DNB service returned an error status: {dnb_response.status_code}'
        raise DNBServiceError(error_message, dnb_response.status_code)

    return dnb_response.json()


def _create_investigation(payload, request=None):
    """
    Submit change request to dnb-service.
    """
    if not settings.DNB_SERVICE_BASE_URL:
        raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')

    api_client = _get_api_client(request)
    response = api_client.request(
        'POST',
        'investigation/',
        json=payload,
        timeout=3.0,
    )
    return response


def create_investigation(investigation_data, request=None):
    """
    Submit change request for the company with the given duns_number
    and changes to the dnb-service.
    """
    try:
        dnb_response = _create_investigation(investigation_data, request)

    except ConnectionError as exc:
        error_message = 'Encountered an error connecting to DNB service'
        raise DNBServiceConnectionError(error_message) from exc

    except Timeout as exc:
        error_message = 'Encountered a timeout interacting with DNB service'
        raise DNBServiceTimeoutError(error_message) from exc

    if not dnb_response.ok:
        error_message = f'DNB service returned an error status: {dnb_response.status_code}'
        raise DNBServiceError(error_message, dnb_response.status_code)

    return dnb_response.json()


def _get_api_client(request=None):
    return APIClient(
        settings.DNB_SERVICE_BASE_URL,
        TokenAuth(settings.DNB_SERVICE_TOKEN),
        raise_for_status=False,
        default_timeout=settings.DNB_SERVICE_TIMEOUT,
        request=request,
    )


def validate_company_id(company_id):
    if not is_valid_uuid(company_id):
        raise APIBadRequestException(f'company id "{company_id}" is not valid')

    company = Company.objects.filter(id=company_id).values_list('duns_number', flat=True)

    if not company:
        raise APINotFoundException(f'company {company_id} not found')

    duns_number = company.first()
    if company and not duns_number:
        raise APIBadRequestException(f'company {company_id} does not contain a duns number')

    hierarchy_serializer = DNBCompanyHierarchySerializer(data={'duns_number': duns_number})
    hierarchy_serializer.is_valid(raise_exception=True)

    return duns_number


def get_full_company_hierarchy_data(duns_number) -> HierarchyData:
    """
    Get a full set of company hierarchy data direct from the dnb service
    """
    if not settings.DNB_SERVICE_BASE_URL:
        raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')

    cache_key = f'family_tree_{duns_number}'
    cache_value = cache.get(cache_key)

    if cache_value:
        return cache_value

    def api_request(api_client):
        return api_client.request(
            'POST',
            'companies/hierarchy/search/',
            json={'duns_number': duns_number},
            timeout=10.0,
        )

    response_data = call_api_request_with_exception_handling(api_request).json()

    hierarchy_data = HierarchyData(
        data=response_data.get('family_tree_members'),
        count=response_data.get('global_ultimate_family_tree_members_count'),
        reduced=False,
    )

    # only cache successful dnb calls
    one_day_timeout = int(timedelta(days=1).total_seconds())
    cache.set(cache_key, hierarchy_data, one_day_timeout)

    return hierarchy_data


def get_company_hierarchy_data(duns_number) -> HierarchyData:
    """
    Get company hierarchy data
    """
    companies_count = get_company_hierarchy_count(duns_number)
    if companies_count > MAX_COMPANIES_IN_TREE_COUNT:
        return get_reduced_company_hierarchy_data(duns_number)

    return get_full_company_hierarchy_data(duns_number)


def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


def _merge_columns_into_single_column(df, key: str, columns: list, nested_objects=None):
    """
    Merge each of the columns in the columns list into a single column with the name
    provided in the key argument
    """
    dataframe_rows = (
        df.reindex(columns=columns).replace([np.nan], [None]).to_dict(orient='records')
    )
    for index, dataframe_row in enumerate(dataframe_rows):
        if all(value is None for value in dataframe_row.values()):
            dataframe_rows[index] = None
        else:
            for col in columns:
                dataframe_row[col.replace(f'{key}.', '')] = dataframe_row.pop(col)
            if nested_objects:
                for nested_object_key, nested_object_value in nested_objects.items():
                    dataframe_row[nested_object_key] = {}

                    for column_key, column_value in nested_object_value.items():
                        dataframe_row[nested_object_key][column_key] = dataframe_row.pop(
                            column_value,
                        )
                    if all(
                        nested_value is None
                        for nested_value in dataframe_row[nested_object_key].values()
                    ):
                        dataframe_row[nested_object_key] = None

    df[key] = dataframe_rows


def _move_requested_duns_to_start_of_subsidiary_list(dataframe, duns_number):
    """
    Move the dataframe row that matches the provided duns number to the start of it's parent
    subsidiary list
    """
    requested_duns_row = dataframe.loc[dataframe['duns'] == duns_number]

    requested_duns_sibling_rows = dataframe.loc[
        dataframe['corporateLinkage.parent.duns']
        == requested_duns_row['corporateLinkage.parent.duns'].values[0]
    ]

    if requested_duns_sibling_rows.empty is False:
        first_subsidiary_index = requested_duns_sibling_rows.head(1).index.item()
        requested_subsidiary_index = requested_duns_row.index.item()
        if first_subsidiary_index != requested_subsidiary_index:
            dataframe.iloc[first_subsidiary_index], dataframe.iloc[requested_subsidiary_index] = (
                dataframe.iloc[requested_subsidiary_index].copy(),
                dataframe.iloc[first_subsidiary_index].copy(),
            )


def create_company_tree(companies: list, duns_number):
    company_hierarchy_dataframe = create_company_hierarchy_dataframe(companies, duns_number)

    root = dataframe_to_tree_by_relation(
        company_hierarchy_dataframe,
        child_col='duns',
        parent_col='corporateLinkage.parent.duns',
    )

    nested_tree = tree_to_nested_dict(
        root,
        name_key='duns_number',
        child_key='subsidiaries',
        attr_dict={
            'primaryName': 'name',
            'companyId': 'id',
            'corporateLinkage.hierarchyLevel': 'hierarchy',
            'ukRegion': 'uk_region',
            'address': 'address',
            'registeredAddress': 'registered_address',
            'sector': 'sector',
            'latestInteractionDate': 'latest_interaction_date',
            'archived': 'archived',
            'numberOfEmployees': 'number_of_employees',
            'oneListTier': 'one_list_tier',
        },
    )

    return nested_tree


def create_company_hierarchy_dataframe(family_tree_members: list, duns_number):
    """
    Create a dataframe from the list of family tree members
    """
    append_datahub_details(family_tree_members)

    normalized_df = pd.json_normalize(family_tree_members)
    normalized_df.replace([np.nan], [None], inplace=True)
    if len(family_tree_members) == 1:
        normalized_df['corporateLinkage.parent.duns'] = None

    _merge_columns_into_single_column(normalized_df, 'sector', ['sector.id', 'sector.name'])
    _merge_columns_into_single_column(normalized_df, 'ukRegion', ['ukRegion.id', 'ukRegion.name'])
    _merge_columns_into_single_column(
        normalized_df,
        'oneListTier',
        ['oneListTier.id', 'oneListTier.name'],
    )
    _merge_columns_into_single_column(
        normalized_df,
        'address',
        [
            'address.line_1',
            'address.line_2',
            'address.town',
            'address.county',
            'address.postcode',
            'address.country.id',
            'address.country.name',
        ],
        {'country': {'id': 'country.id', 'name': 'country.name'}},
    )
    _merge_columns_into_single_column(
        normalized_df,
        'registeredAddress',
        [
            'registeredAddress.line_1',
            'registeredAddress.line_2',
            'registeredAddress.town',
            'registeredAddress.county',
            'registeredAddress.postcode',
            'registeredAddress.country.id',
            'registeredAddress.country.name',
        ],
        {
            'country': {'id': 'country.id', 'name': 'country.name'},
        },
    )
    _move_requested_duns_to_start_of_subsidiary_list(normalized_df, duns_number)
    return normalized_df


def append_datahub_details(family_tree_members: list):
    """
    Appended any known datahub details to the list of family tree members provided
    """
    family_tree_members_duns = [object['duns'] for object in family_tree_members]
    family_tree_members_datahub_details = load_datahub_details(family_tree_members_duns)
    empty_address = {
        'line_1': None,
        'line_2': None,
        'town': None,
        'county': None,
        'postcode': None,
        'country': {'id': None, 'name': None},
    }
    empty_id_name = {'id': None, 'name': None}

    for family_member in family_tree_members:
        duns_number_to_find = family_member['duns']
        family_member['companyId'] = None
        family_member['ukRegion'] = empty_id_name
        family_member['address'] = empty_address
        family_member['registeredAddress'] = empty_address
        family_member['sector'] = empty_id_name
        family_member['latestInteractionDate'] = None
        family_member['archived'] = False
        family_member['oneListTier'] = empty_id_name
        number_of_employees = family_member.get('numberOfEmployees')
        if isinstance(number_of_employees, list):
            family_member['numberOfEmployees'] = number_of_employees[0].get('value')
        for datahub_detail in family_tree_members_datahub_details:
            if duns_number_to_find == datahub_detail.get('duns_number'):
                family_member['primaryName'] = datahub_detail.get('name')
                family_member['companyId'] = datahub_detail.get('id')
                family_member['ukRegion'] = datahub_detail.get('uk_region')
                family_member['address'] = datahub_detail.get('address')
                family_member['registeredAddress'] = datahub_detail.get('registered_address')
                family_member['sector'] = datahub_detail.get('sector')
                family_member['latestInteractionDate'] = datahub_detail.get(
                    'latest_interaction_date',
                )
                family_member['archived'] = datahub_detail.get('archived')
                family_member['oneListTier'] = datahub_detail.get('one_list_tier')
                if not number_of_employees:
                    family_member['numberOfEmployees'] = datahub_detail.get('number_of_employees')
                break  # Stop once we've found the match


def create_related_company_dataframe(family_tree_members: list):
    """
    Create a dataframe from the list of family tree members that only appends with
    Data Hub company IDs
    """
    normalized_df = pd.json_normalize(family_tree_members)
    normalized_df.replace([np.nan], [None], inplace=True)
    if len(family_tree_members) == 1:
        normalized_df['corporateLinkage.parent.duns'] = None

    return normalized_df


def get_datahub_company_ids(family_tree_members: list):
    """
    Get company ids for related companies returned from D&B

    """
    family_tree_members_datahub_details = get_search_by_entities_query(
        [SearchCompany],
        term='',
        filter_data={'duns_number': family_tree_members},
        fields_to_include='id',
    ).execute()
    related_company_ids = []

    for related_company in family_tree_members_datahub_details:
        related_company_ids.append(related_company.id)
    return related_company_ids


def _batch_list(list, number_items):
    """
    Create a list of lists, with the maximum number of items in each list set to the number
    provided in number_items
    Args:
        list (_type_): The list to create a batch of lists from
        number_items (_type_): The maximum number of items
    Returns:
        A list of lists, with each inner list containing at most the number_items. The final inner
        list may contain less then the number_items
    """
    list = iter(list)
    return iter(lambda: tuple(islice(list, number_items)), ())


def load_datahub_details(family_tree_members_duns):
    """
    Load any known datahub details for the duns numbers provided
    """
    # Because of the way the get_search_by_entities_query creates an opensearch query, which is
    # to convert every duns number into a separate match filter, we need to batch the opensearch
    # queries so only 1024 are sent at a time

    results = []
    for batch_of_duns_numbers in _batch_list(
        family_tree_members_duns,
        MAX_DUNS_NUMBERS_PER_REQUEST,
    ):
        query = get_search_by_entities_query(
            [SearchCompany],
            term='',
            filter_data={'duns_number': list(batch_of_duns_numbers)},
            fields_to_include=(
                'id',
                'name',
                'duns_number',
                'uk_region',
                'address',
                'registered_address',
                'sector',
                'latest_interaction_date',
                'archived',
                'one_list_tier',
                'number_of_employees',
            ),
        )[0:MAX_DUNS_NUMBERS_PER_REQUEST]
        opensearch_results = execute_search_query(query)
        results.extend(opensearch_results.hits)

    return [result.to_dict() for result in results]


def get_company_hierarchy_count(duns_number):
    """
    Get the count of companies in the hierarchy
    """
    if not settings.DNB_SERVICE_BASE_URL:
        raise ImproperlyConfigured('The setting DNB_SERVICE_BASE_URL has not been set')

    cache_key = f'family_tree_count_{duns_number}'
    cache_value = cache.get(cache_key)

    if cache_value:
        return cache_value

    def api_request(api_client):
        return api_client.request(
            'POST',
            'companies/hierarchy/search/count',
            json={'duns_number': duns_number},
            timeout=3.0,
        )

    companies_count = call_api_request_with_exception_handling(api_request).json()
    if companies_count > 0:
        companies_count = companies_count - 1

    # only cache successful dnb calls
    one_day_timeout = int(timedelta(days=1).total_seconds())
    cache.set(cache_key, companies_count, one_day_timeout)

    return companies_count


def call_api_request_with_exception_handling(api_request_function, statsd_stat=None):
    """
    Call the dnb service api client and handle any common errors
    """
    api_client = _get_api_client()
    try:
        result = api_request_function(api_client)
        if statsd_stat:
            statsd.incr(f'{statsd_stat}.{result.status_code}')

    except APIBadGatewayException as exc:
        error_message = 'Encountered an error connecting to DNB service'
        logger.error(error_message)
        raise DNBServiceConnectionError(error_message) from exc

    except ConnectionError as exc:
        error_message = 'Encountered an error connecting to DNB service'
        logger.error(error_message)
        raise DNBServiceConnectionError(error_message) from exc

    except Timeout as exc:
        error_message = 'Encountered a timeout interacting with DNB service'
        logger.error(error_message)
        raise DNBServiceTimeoutError(error_message) from exc

    if not result.ok:
        error_message = f'DNB service returned an error status: {result.status_code}'
        logger.error(error_message)
        raise DNBServiceError(error_message, result.status_code)

    return result


def get_reduced_company_hierarchy_data(duns_number) -> HierarchyData:
    """
    Get company data that only includes direct parents of the duns number
    """
    hierarchy = []
    while duns_number:
        company_response = get_cached_dnb_company(duns_number)
        formatted_company = format_company_for_family_tree(company_response)
        hierarchy.append(formatted_company)
        if formatted_company.get('corporateLinkage.parent.duns'):
            duns_number = formatted_company.get('corporateLinkage.parent.duns')
        else:
            duns_number = None

    index = 1  # index needs to sit outside, as the reversed function also reverses the index
    for hierarchy_item in reversed(hierarchy):
        hierarchy_item['corporateLinkage.hierarchyLevel'] = index
        index += 1

    return HierarchyData(data=hierarchy, count=len(hierarchy), reduced=True)


def get_datahub_ids_for_dnb_service_company_hierarchy(
    include_parent_companies,
    include_subsidiary_companies,
    company_id,
):
    duns_number = validate_company_id(company_id)
    print('***** duns_number', duns_number)
    try:
        response = get_company_hierarchy_data(duns_number)
    except (
        DNBServiceConnectionError,
        DNBServiceTimeoutError,
        DNBServiceError,
    ) as exc:
        raise APIUpstreamException(str(exc))

    family_tree_members = response.data
    json_response = {'related_companies': [], 'reduced_tree': None}
    if not family_tree_members:
        return Response(json_response)

    company_hierarchy_dataframe = create_related_company_dataframe(family_tree_members)

    root = dataframe_to_tree_by_relation(
        company_hierarchy_dataframe,
        child_col='duns',
        parent_col='corporateLinkage.parent.duns',
    )

    duns_node = find(root, lambda node: node.name == duns_number)

    related_duns = []
    json_response['reduced_tree'] = response.reduced
    if include_parent_companies:
        ancestors_duns = duns_node.ancestors
        for ancestor_duns_number in ancestors_duns:
            related_duns.append(ancestor_duns_number.node_name)

    if include_subsidiary_companies:
        descendants_duns = duns_node.descendants
        for descendant_duns_number in descendants_duns:
            related_duns.append(descendant_duns_number.node_name)

    if related_duns:
        json_response['related_companies'] = get_datahub_company_ids(related_duns)

    return json_response


def get_cached_dnb_company(duns_number):
    """
    Get the dnb company from the cache if it exists. If not, call the dnb api and save the result
    in the cache before returning the company
    """
    cache_key = f'dnb_company_{duns_number}'
    cache_value = cache.get(cache_key)

    if cache_value:
        return cache_value

    company_response = get_dnb_company_data(duns_number)

    # only cache successful dnb calls
    one_day_timeout = int(timedelta(days=1).total_seconds())
    cache.set(cache_key, company_response, one_day_timeout)

    return company_response


def format_company_for_family_tree(company):
    """
    Format the response from the search api to the format needed by the family tree
    """
    company_object = {
        'duns': None,
        'corporateLinkage.parent.duns': None,
        'primaryName': None,
    }
    if company:
        parent_duns_number = company.get('parent_duns_number')
        company_object['duns'] = company.get('duns_number')
        company_object['corporateLinkage.parent.duns'] = (
            parent_duns_number if parent_duns_number else None
        )
        company_object['primaryName'] = company.get('primary_name')

    return company_object
