from datetime import date
from os import path
from unittest import mock
from uuid import UUID

import pytest
from django.db import connection

from datahub.company.ch_constants import CSV_RELEVANT_FIELDS
from datahub.company.management.commands import sync_ch
from datahub.company.models import CompaniesHouseCompany
from datahub.company.test.factories import CompaniesHouseCompanyFactory
from datahub.core.constants import Country

pytestmark = pytest.mark.django_db


@mock.patch('datahub.company.management.commands.sync_ch.requests')
def test_fetching_ch_urls_list(requests_mock):
    """Test page parsing."""
    requests_mock.get().content = b"""
    <html>
    <body>
    <div class="omega">
    <a href="test1">Test1</a>
    <a href="test2">Test2</a>
    </div>
    </body>
    </html>
    """

    assert sync_ch.get_ch_latest_dump_file_list('https://example.com/anything.html') == [
        'https://example.com/test1',
        'https://example.com/test2',
    ]


def test_column_filtering():
    """Test filtering and date parse."""
    test_dict = dict(irrelevant=True, incorporation_date='12/03/1999')

    result = sync_ch.transform_ch_row(test_dict)

    assert set(result.keys()) > set(CSV_RELEVANT_FIELDS)
    assert result['incorporation_date'] == date(1999, 3, 12)


def test_missing_registered_address_town():
    """Test missing registered address town."""
    test_dict = {}

    result = sync_ch.transform_ch_row(test_dict)

    assert set(result.keys()) > set(CSV_RELEVANT_FIELDS)
    assert result['registered_address_town'] == ''


def test_empty_registered_address_town():
    """Test empty registered address town."""
    test_dict = {
        'registered_address_1': '3 Lions Lane',
        'registered_address_town': '',
    }

    result = sync_ch.transform_ch_row(test_dict)

    assert set(result.keys()) > set(CSV_RELEVANT_FIELDS)
    assert result['registered_address_town'] == ','


def test_present_registered_address_town():
    """Test present registered address town."""
    test_dict = {
        'registered_address_town': 'Meow town',
    }

    result = sync_ch.transform_ch_row(test_dict)

    assert set(result.keys()) > set(CSV_RELEVANT_FIELDS)
    assert result['registered_address_town'] == 'Meow town'


def test_empty_address_town_when_no_address():
    """Test registered address town is empty when no address."""
    test_dict = {
        'registered_address_1': '',
        'registered_address_town': '',
    }

    result = sync_ch.transform_ch_row(test_dict)

    assert set(result.keys()) > set(CSV_RELEVANT_FIELDS)
    assert result['registered_address_town'] == ''


def test_unzip_and_csv_read_on_the_fly():
    """Test on-the-fly extract."""
    fixture_loc = path.join(path.dirname(__file__), 'fixtures', 'CH_data_test.zip')

    with open(fixture_loc, 'rb') as f:
        with sync_ch.open_ch_zipped_csv(f) as csv_reader:
            result = list(csv_reader)

            assert len(result) == 201


@pytest.mark.parametrize(
    'row,num_results',
    (
        ({'company_category': 'Private Limited Company'}, 1),
        ({'company_category': 'public limited company'}, 1),
        ({'company_category': 'registered society'}, 0),
    ),
)
def test_process_row_company_filtering(row, num_results):
    """Tests filtering of companies with an irrelevant type."""
    processed = list(sync_ch.process_row(row))
    assert len(processed) == num_results


def test_process_rows_record():
    """Tests that records are updated or inserted as needed."""
    existing_ch_company = CompaniesHouseCompanyFactory(
        company_number='00000001',
        name='old name',
    )

    existing_record_update_data = {
        'company_number': '00000001',
        'company_category': 'company cat 1',
        'company_status': 'status 1',
        'incorporation_date': date(2017, 1, 1),
        'name': 'name 1',
        'registered_address_1': 'add 1-1',
        'registered_address_2': 'add 1-2',
        'registered_address_country_id': UUID(Country.united_kingdom.value.id),
        'registered_address_county': 'county 1',
        'registered_address_postcode': 'postcode 1',
        'registered_address_town': 'town 1',
        'sic_code_1': 'sic code 1-1',
        'sic_code_2': 'sic code 1-2',
        'sic_code_3': 'sic code 1-3',
        'sic_code_4': 'sic code 1-4',
        'uri': 'uri 1',
    }
    new_record_data = {
        'company_number': '00000002',
        'company_category': 'company cat 2',
        'company_status': 'status 2',
        'incorporation_date': date(2016, 12, 1),
        'name': 'name 2',
        'registered_address_1': 'add 2-1',
        'registered_address_2': 'add 2-2',
        'registered_address_country_id': UUID(Country.united_kingdom.value.id),
        'registered_address_county': 'county 2',
        'registered_address_postcode': 'postcode 2',
        'registered_address_town': 'town 2',
        'sic_code_1': 'sic code 2-1',
        'sic_code_2': 'sic code 2-2',
        'sic_code_3': 'sic code 2-3',
        'sic_code_4': 'sic code 2-4',
        'uri': 'uri 2',
    }

    with connection.cursor() as cursor:
        syncer = sync_ch.CHSynchroniser()
        syncer._process_batch(cursor, [existing_record_update_data, new_record_data])

    existing_ch_company.refresh_from_db()
    actual_updated_data = {
        field: getattr(existing_ch_company, field) for field in existing_record_update_data
    }

    new_ch_company = CompaniesHouseCompany.objects.get(
        company_number=new_record_data['company_number'],
    )
    actual_new_data = {
        field: getattr(new_ch_company, field) for field in new_record_data
    }

    assert CompaniesHouseCompany.objects.count() == 2
    assert actual_updated_data == existing_record_update_data
    assert actual_new_data == new_record_data


@pytest.mark.django_db
@mock.patch('datahub.company.management.commands.sync_ch.stream_to_file_pointer', mock.MagicMock())
@mock.patch('datahub.company.management.commands.sync_ch.get_ch_latest_dump_file_list')
def test_full_ch_sync(file_list_mock, settings):
    """Test the whole process."""
    settings.BULK_INSERT_BATCH_SIZE = 2
    file_list_mock.return_value = ['irrelevant']
    fixture_loc = path.join(path.dirname(__file__), 'fixtures', 'CH_data_test.zip')

    syncer = sync_ch.CHSynchroniser()
    syncer.run(tmp_file_creator=lambda: open(fixture_loc, 'rb'))

    # Two companies with irrelevant types excluded
    assert CompaniesHouseCompany.objects.count() == 198


@pytest.mark.django_db
@mock.patch('datahub.company.management.commands.sync_ch.stream_to_file_pointer', mock.MagicMock())
@mock.patch('datahub.company.management.commands.sync_ch.get_ch_latest_dump_file_list')
def test_simulated_ch_sync(file_list_mock, settings):
    """Test the whole process."""
    settings.BULK_INSERT_BATCH_SIZE = 2
    file_list_mock.return_value = ['irrelevant']
    fixture_loc = path.join(path.dirname(__file__), 'fixtures', 'CH_data_test.zip')

    syncer = sync_ch.CHSynchroniser(simulate=True)
    syncer.run(tmp_file_creator=lambda: open(fixture_loc, 'rb'))

    # No companies house companies should have been synced
    assert CompaniesHouseCompany.objects.count() == 0
