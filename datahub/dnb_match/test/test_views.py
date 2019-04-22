"""Tests for matching information views."""

from uuid import uuid4

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import APITestMixin
from datahub.core.test_utils import create_test_user
from datahub.dnb_match.test.factories import DnBMatchingCSVRecord, DnBMatchingResultFactory
from datahub.dnb_match.views import _replace_dnb_country_fields


def _create_match_result_selected():
    """Create match result test dictionary."""
    return {
        'dnb_match': {
            'duns_number': '111',
            'name': 'NAME OF A COMPANY',
            'country': 'United Kingdom',
            'global_ultimate_duns_number': '112',
            'global_ultimate_name': 'NAME OF A GLOBAL COMPANY',
            'global_ultimate_country': 'United Kingdom',
        },
        'matched_by': 'data-science',
    }


def _create_match_result_no_match(reason, description=None, candidates=None):
    """Create no match result test dictionary."""
    no_match = {
        'reason': reason,
    }
    if description:
        no_match['description'] = description
    if candidates:
        no_match['candidates'] = candidates

    return {
        'no_match': no_match,
        'matched_by': 'adviser',
    }


class TestMatchingInformationView(APITestMixin):
    """Tests for the matching information view."""

    def test_access_is_denied_if_without_permissions(self):
        """Test that a 403 is returned if the user has no permissions."""
        company = CompanyFactory()
        user = create_test_user(permission_codenames=[])
        api_client = self.create_api_client(user=user)

        url = reverse(
            'api-v4:dnb-match:item',
            kwargs={
                'company_pk': company.pk,
            },
        )

        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_get_match_information_of_company_that_doesnt_exist(self):
        """Test that a 404 is returned if company doesn't exist."""
        url = reverse(
            'api-v4:dnb-match:item',
            kwargs={
                'company_pk': uuid4(),
            },
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize('result', (
        _create_match_result_selected(),
        _create_match_result_no_match('not_listed'),
        _create_match_result_no_match('more_than_one', candidates=['111', '222', '333']),
        _create_match_result_no_match('not_confident'),
        _create_match_result_no_match('other', description='These candidates are out of place.'),
    ))
    def test_matching_information(self, result):
        """Tests matching information endpoint."""
        company = _create_company_with_matching_result_and_candidates(
            result=result,
            candidates=_get_match_candidates(),
        )

        url = reverse(
            'api-v4:dnb-match:item',
            kwargs={
                'company_pk': company.pk,
            },
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert 'result' in response_data

        expected_result = _replace_dnb_country_fields({'result': result})

        assert response_data['result'] == expected_result['result']
        assert 'candidates' in response_data
        assert response_data['candidates'] == [
            {
                'duns_number': 12345,
                'name': 'test name',
                'global_ultimate_duns_number': 12345,
                'global_ultimate_name': 'test name global',
                'global_ultimate_country': {
                    'id': '81756b9a-5d95-e211-a939-e4115bead28a',
                    'name': 'United States',
                },
                'address_1': '1st LTD street',
                'address_2': '',
                'address_town': 'London',
                'address_postcode': 'SW1A 1AA',
                'address_country': {
                    'id': '81756b9a-5d95-e211-a939-e4115bead28a',
                    'name': 'United States',
                },
                'confidence': 10,
                'source': 'cats',
            },
            {
                'duns_number': 12346,
                'name': 'test name',
                'global_ultimate_duns_number': 12345,
                'global_ultimate_name': 'test name global',
                'global_ultimate_country': {
                    'id': '81756b9a-5d95-e211-a939-e4115bead28a',
                    'name': 'United States',
                },
                'address_1': '1st LTD street',
                'address_2': '',
                'address_town': 'London',
                'address_postcode': 'SW1A 1AA',
                'address_country': {
                    'id': '81756b9a-5d95-e211-a939-e4115bead28a',
                    'name': 'United States',
                },
                'confidence': 10,
                'source': 'cats',
            },
        ]

    def test_can_get_information_if_matching_records_dont_exist(self):
        """
        Tests that matching information endpoint returns information if corresponding matching
        records don't exist.
        """
        company = CompanyFactory()
        url = reverse(
            'api-v4:dnb-match:item',
            kwargs={
                'company_pk': company.pk,
            },
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert 'result' in response_data
        assert response_data['result'] == {}
        assert 'candidates' in response_data
        assert response_data['candidates'] == []


class TestSelectMatchView(APITestMixin):
    """Tests for the select a match view."""

    def test_access_is_denied_if_without_permissions(self):
        """Test that a 403 is returned if the user has no permissions."""
        company = CompanyFactory()
        user = create_test_user(permission_codenames=[])
        api_client = self.create_api_client(user=user)

        url = reverse(
            'api-v4:dnb-match:select-match',
            kwargs={
                'company_pk': company.pk,
            },
        )

        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_match_company_that_doesnt_exist(self):
        """Test that a 404 is returned if company doesn't exist."""
        url = reverse(
            'api-v4:dnb-match:select-match',
            kwargs={
                'company_pk': uuid4(),
            },
        )

        response = self.api_client.post(url, {'duns_number': '12345'})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_select_match(self):
        """Tests if candidate can be selected."""
        company = _create_company_with_matching_result_and_candidates(
            candidates=_get_match_candidates(),
        )

        url = reverse(
            'api-v4:dnb-match:select-match',
            kwargs={
                'company_pk': company.pk,
            },
        )

        data = {
            'duns_number': 12345,
        }
        response = self.api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert 'result' in response_data
        assert response_data['result'] == {
            'dnb_match': {
                'name': 'test name',
                'duns_number': 12345,
                'country': {
                    'id': '81756b9a-5d95-e211-a939-e4115bead28a',
                    'name': 'United States',
                },
                'global_ultimate_name': 'test name global',
                'global_ultimate_country': {
                    'id': '81756b9a-5d95-e211-a939-e4115bead28a',
                    'name': 'United States',
                },
                'global_ultimate_duns_number': 12345,
            },
            'matched_by': 'adviser',
            'adviser': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name,
            },
        }

    @pytest.mark.parametrize('body,expected', (
        (
            {},
            {'duns_number': ['This field is required.']},
        ),
        (
            {'nothing_to_declare': 'cats'},
            {'duns_number': ['This field is required.']},
        ),
        (
            {'duns_numbers': ['cats', 'tigers', 'manuls']},
            {'duns_number': ['This field is required.']},
        ),
    ))
    def test_cant_select_match_using_invalid_request(self, body, expected):
        """Tests if candidate cannot be selected when sending invalid request."""
        company = _create_company_with_matching_result_and_candidates(
            candidates=_get_match_candidates(),
        )

        url = reverse(
            'api-v4:dnb-match:select-match',
            kwargs={
                'company_pk': company.pk,
            },
        )
        response = self.api_client.post(url, body)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected


class TestSelectNoMatch(APITestMixin):
    """Tests for select no match view."""

    def test_access_is_denied_if_without_permissions(self):
        """Test that a 403 is returned if the user has no permissions."""
        company = CompanyFactory()
        user = create_test_user(permission_codenames=[])
        api_client = self.create_api_client(user=user)

        url = reverse(
            'api-v4:dnb-match:select-no-match',
            kwargs={
                'company_pk': company.pk,
            },
        )

        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_select_no_match_for_company_that_doesnt_exist(self):
        """Test that a 404 is returned if company doesn't exist."""
        url = reverse(
            'api-v4:dnb-match:select-no-match',
            kwargs={
                'company_pk': uuid4(),
            },
        )

        response = self.api_client.post(url, {'reason': 'not_listed'})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize('body', (
        _create_match_result_no_match('not_listed'),
        _create_match_result_no_match('more_than_one', candidates=['111', '222', '333']),
        _create_match_result_no_match('not_confident'),
        _create_match_result_no_match('other', description='These candidates are out of place.'),
    ))
    def test_select_no_match(self, body):
        """Tests if no match can be selected."""
        company = _create_company_with_matching_result_and_candidates(
            candidates=_get_match_candidates(),
        )

        url = reverse(
            'api-v4:dnb-match:select-no-match',
            kwargs={
                'company_pk': company.pk,
            },
        )
        response = self.api_client.post(url, body['no_match'])
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert 'result' in response_data
        assert response_data['result'] == {
            'no_match': body['no_match'],
            'matched_by': 'adviser',
            'adviser': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name,
            },
        }

    @pytest.mark.parametrize('body,expected', (
        (
            _create_match_result_no_match('what'), {'reason': ['"what" is not a valid choice.']},
        ),
        (
            _create_match_result_no_match('No reason at all!'),
            {'reason': ['"No reason at all!" is not a valid choice.']},
        ),
        (
            {},
            {'reason': ['This field is required.']},
        ),
        (
            {'nothing_to_declare': 'cats'},
            {'reason': ['This field is required.']},
        ),
        (
            _create_match_result_no_match('more_than_one', candidates='123'),
            {'candidates': ['Expected a list of items but got type "str".']},
        ),
        (
            {'reason': 'other'},
            {'description': ['The "description" is required if the reason is "other".']},
        ),
        (
            {'reason': 'more_than_one'},
            {'candidates': [
                'List of candidates is required if the reason is "more_than_one".',
            ]},
        ),
        (
            {'reason': 'not_listed', 'candidates': ['111', '333']},
            {'non_field_errors': [
                'If the reason is "not_listed" or "not_confident", other fields should not '
                'need to be filled.',
            ]},
        ),
        (
            {'reason': 'not_confident', 'description': 'is not confident?'},
            {
                'non_field_errors': [
                    'If the reason is "not_listed" or "not_confident", other fields should not '
                    'need to be filled.',
                ],
            },
        ),
    ))
    def test_cant_select_no_match_with_invalid_request(self, body, expected):
        """Tests if no match can be selected."""
        company = _create_company_with_matching_result_and_candidates(
            candidates=_get_match_candidates(),
        )

        url = reverse(
            'api-v4:dnb-match:select-no-match',
            kwargs={
                'company_pk': company.pk,
            },
        )

        response = self.api_client.post(url, body['no_match'] if 'no_match' in body else body)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected


def _create_company_with_matching_result_and_candidates(result=None, candidates=None):
    """Creates company with matching result and matching candidates."""
    if not result:
        result = {}
    if not candidates:
        candidates = {}

    company = CompanyFactory()

    DnBMatchingResultFactory(company=company, data=result)
    DnBMatchingCSVRecord(company_id=company.pk, data=candidates)

    return company


def _get_match_candidates():
    return [
        {
            'duns_number': 12345,
            'name': 'test name',
            'global_ultimate_duns_number': 12345,
            'global_ultimate_name': 'test name global',
            'global_ultimate_country': 'USA',
            'address_1': '1st LTD street',
            'address_2': '',
            'address_town': 'London',
            'address_postcode': 'SW1A 1AA',
            'address_country': 'USA',
            'confidence': 10,
            'source': 'cats',
        },
        {
            'duns_number': 12346,
            'name': 'test name',
            'global_ultimate_duns_number': 12345,
            'global_ultimate_name': 'test name global',
            'global_ultimate_country': 'USA',
            'address_1': '1st LTD street',
            'address_2': '',
            'address_town': 'London',
            'address_postcode': 'SW1A 1AA',
            'address_country': {
                'id': '81756b9a-5d95-e211-a939-e4115bead28a',
                'name': 'United States',
            },
            'confidence': 10,
            'source': 'cats',
        },
    ]
