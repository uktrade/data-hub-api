import os
from unittest.mock import (
    patch,
)

import factory
import pytest
from django.core.management import (
    call_command,
)
from freezegun import (
    freeze_time,
)

from datahub.company.models.company import (
    Company,
)
from datahub.company.test.factories import (
    CompanyFactory,
)


@pytest.mark.django_db
def test_import_uses_hawk_authentication(requests_mock):
    """Tests that the import uses Hawk authentication"""
    first_page_url = os.environ['ACTIVITY_STREAM_OUTGOING_URL']
    second_page_url = 'http://any.domain/second-page'

    requests_mock.get(first_page_url, json=_activity_stream_page([], {
        'next': second_page_url,
    }))
    requests_mock.get(second_page_url, json=_activity_stream_page([], {}))

    with \
            freeze_time('2014-01-05'), \
            patch('os.urandom', side_effect=[b'abcdefghij', b'klmnopqrst']):
        call_command('import_from_activity_stream')

    # A bit brittle, but should only fail incorrectly if the query changes.
    # Other failures would indicate broken production code
    assert requests_mock.request_history[0].headers['Authorization'] == (
        'Hawk mac="leEJ6VOZEKhaMgkYwQq896kntnnbteDxvaY4RTPXVPA=", '
        'hash="dS+ssqlhGsDWmIyuB0Hp50MegDTXquYnjMGsQcLFJLk=", '
        'id="some-outgoing-id", ts="1388880000", nonce="YWJjZG"'
    )
    assert requests_mock.request_history[1].headers['Authorization'] == (
        'Hawk mac="TNndfzO/Lt5KiHdb7qYLu7ofgeNchjs8LjIpbd+ASUU=", '
        'hash="IE2cO/h4K12HFJexL6Qia8r5tmQ/7LzRfogctPjL+UI=", '
        'id="some-outgoing-id", ts="1388880000", nonce="a2xtbm"'
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'existing_company_numbers,as_paginated_company_numbers',
    (
        (
            # Single empty page
            [],
            [[]],
        ),
        (
            # Two empty pages
            [],
            [[], []],
        ),
        (
            # Single new company
            [],
            [['01234560']],
        ),
        (
            # Single new company, repeated in stream on single page
            [],
            [['01234560', '01234560']],
        ),
        (
            # Single new company, repeated in stream on two pages
            [],
            [['01234560'], ['01234560']],
        ),
        (
            # Two new companies on single page
            [],
            [['01234560', '01234561']],
        ),
        (
            # Two new companies on single page + empty page
            [],
            [['01234560', '01234561'], []],
        ),
        (
            # Two new companies over two pages
            [],
            [['01234560'], ['01234561']],
        ),
        (
            # Two new companies over two pages + empty page at end
            [],
            [['01234560'], ['01234561'], []],
        ),
        (
            # Two new companies over two pages + empty page at start
            [],
            [[], ['01234560'], ['01234561']],
        ),
        (
            # Two new companies over two pages + empty page in middle
            [],
            [['01234560'], [], ['01234561']],
        ),
        (
            # Two new companies over two pages + empty page in middle and end
            [],
            [['01234560'], [], ['01234561'], []],
        ),
        (
            # No new companies, one existing
            ['01234560'],
            [['01234560']],
        ),
        (
            # No new companies, two existing, single page
            ['01234560', '01234561'],
            [['01234560', '01234561']],
        ),
        (
            # No new companies, two existing, two pages
            ['01234560', '01234561'],
            [['01234560'], ['01234561']],
        ),
        (
            # One new company, one existing which is first on single page
            ['01234560'],
            [['01234560', '01234561']],
        ),
        (
            # One new company, one existing which is second of two pages
            ['01234560'],
            [['01234560'], ['01234561']],
        ),
        (
            # One new company, one existing which is second on single page
            ['01234561'],
            [['01234560', '01234561']],
        ),
        (
            # One new company, one existing which is second on two pages
            ['01234561'],
            [['01234560'], ['01234561']],
        ),
    ),
)
def test_imports_companies_without_duplicates(existing_company_numbers,
                                              as_paginated_company_numbers, requests_mock):
    """Tests that all non-existing companies are created, with no duplicates are created"""
    # Create all existing companies
    CompanyFactory.create_batch(
        len(existing_company_numbers),
        company_number=factory.Iterator(existing_company_numbers),
    )

    first_page_url = os.environ['ACTIVITY_STREAM_OUTGOING_URL']

    # Mock the activity stream that gives company numbers to create
    num_pages = len(as_paginated_company_numbers)
    for i, company_numbers in enumerate(as_paginated_company_numbers):
        is_first_page = i == 0
        is_last_page = i == num_pages - 1
        url = \
            first_page_url if is_first_page else \
            'http://activity.stream/?page=' + str(i)
        next_page_dict = {
            'next': 'http://activity.stream/?page=' + str(i + 1),
        } if not is_last_page else {}
        data_at_url = _activity_stream_page(company_numbers, next_page_dict)
        requests_mock.get(url, json=data_at_url)

    # Run the import from the activity stream
    call_command('import_from_activity_stream')

    # Assert that the initial GET query contains roughly enough information
    # We don't assert on the exact query: this is likely brittle and without
    # much value,  given we can't actually validate that it's correct
    initial_request_body = requests_mock.request_history[0].text
    assert '"Create"' in initial_request_body
    assert '"dit:directory:CompanyVerification"' in initial_request_body

    # Assert that new companies are created, and without duplicates
    company_numbers_that_should_exist = \
        sorted(set(_flatten(as_paginated_company_numbers)).union(existing_company_numbers))
    company_numbers_that_do_exist = sorted(Company.objects.filter(
        company_number__in=company_numbers_that_should_exist,
    ).values_list('company_number', flat=True))
    assert company_numbers_that_should_exist == company_numbers_that_do_exist


def _activity_stream_page(company_numbers, next_page_dict):
    return {
        '@context': [
            'https://www.w3.org/ns/activitystreams', {
                'dit': 'https://www.trade.gov.uk/ns/activitystreams/v1',
            },
        ],
        'type': 'Collection',
        'orderedItems': [
            {
                'object': {
                    'id': 'dit:directory:CompanyVerification:1:Create',
                    'type': ['Document', 'dit:directory:CompanyVerification'],
                    'attributedTo': {
                        'dit:companiesHouseNumber': company_number,
                    },
                },
            } for company_number in company_numbers
        ],
        **next_page_dict,
    }


def _flatten(list_of_lists):
    return [
        item
        for sub_list in list_of_lists
        for item in sub_list
    ]
