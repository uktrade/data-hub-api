from datetime import date
from os import path
from unittest import mock

import pytest
from django.conf import settings

from datahub.company.management.commands import sync_ch
from datahub.company.models import CompaniesHouseCompany


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

    assert set(result.keys()) > set(settings.CH_RELEVANT_FIELDS)
    assert result['incorporation_date'] == date(1999, 3, 12)


def test_missing_registered_address_town():
    """Test missing registered address town."""
    test_dict = {}

    result = sync_ch.transform_ch_row(test_dict)

    assert set(result.keys()) > set(settings.CH_RELEVANT_FIELDS)
    assert result['registered_address_town'] == ''


def test_empty_registered_address_town():
    """Test empty registered address town."""
    test_dict = {
        'registered_address_town': '',
    }

    result = sync_ch.transform_ch_row(test_dict)

    assert set(result.keys()) > set(settings.CH_RELEVANT_FIELDS)
    assert result['registered_address_town'] == ','


def test_present_registered_address_town():
    """Test present registered address town."""
    test_dict = {
        'registered_address_town': 'Meow town'
    }

    result = sync_ch.transform_ch_row(test_dict)

    assert set(result.keys()) > set(settings.CH_RELEVANT_FIELDS)
    assert result['registered_address_town'] == 'Meow town'


def test_unzip_and_csv_read_on_the_fly():
    """Test on-the-fly extract."""
    fixture_loc = path.join(path.dirname(__file__), 'fixtures', 'CH_data_test.zip')

    with open(fixture_loc, 'rb') as f:
        with sync_ch.open_ch_zipped_csv(f) as csv_reader:
            result = list(csv_reader)

            assert len(result) == 201


@pytest.mark.parametrize('row,num_results', (
    ({'company_category': 'Private Limited Company'}, 1),
    ({'company_category': 'public limited company'}, 1),
    ({'company_category': 'registered society'}, 0),
))
def test_process_row_company_filtering(row, num_results):
    """Tests filtering of companies with an irrelevant type."""
    processed = list(sync_ch.process_row(row))
    assert len(processed) == num_results


@pytest.mark.django_db
@mock.patch('datahub.company.management.commands.sync_ch.stream_to_file_pointer', mock.MagicMock())
@mock.patch('datahub.company.management.commands.sync_ch.get_ch_latest_dump_file_list')
def test_full_ch_sync(file_list_mock, settings):
    """Test the whole process."""
    settings.BULK_CREATE_BATCH_SIZE = 2
    file_list_mock.return_value = ['irrelevant']
    fixture_loc = path.join(path.dirname(__file__), 'fixtures', 'CH_data_test.zip')

    sync_ch.sync_ch(tmp_file_creator=lambda: open(fixture_loc, 'rb'))

    # Two companies with irrelevant types excluded
    assert CompaniesHouseCompany.objects.count() == 198


@pytest.mark.django_db
@mock.patch('datahub.company.management.commands.sync_ch.stream_to_file_pointer', mock.MagicMock())
@mock.patch('datahub.company.management.commands.sync_ch.get_ch_latest_dump_file_list')
def test_simulated_ch_sync(file_list_mock, settings):
    """Test the whole process."""
    settings.BULK_CREATE_BATCH_SIZE = 2
    file_list_mock.return_value = ['irrelevant']
    fixture_loc = path.join(path.dirname(__file__), 'fixtures', 'CH_data_test.zip')

    sync_ch.sync_ch(tmp_file_creator=lambda: open(fixture_loc, 'rb'), simulate=True)

    # No companies house companies should have been synced
    assert CompaniesHouseCompany.objects.count() == 0
