
from datetime import date
from os import path
from unittest import mock

import pytest
from django.conf import settings

from datahub.company.management.commands import sync_ch
from datahub.company.models import CompaniesHouseCompany
from datahub.company.test.factories import CompaniesHouseCompanyFactory


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

    assert sync_ch.get_ch_latest_dump_file_list('anything') == ['test1', 'test2']


def test_column_filtering():
    """Test filtering and date parse."""
    test_dict = dict(irrelevant=True, incorporation_date='12/03/1999')

    result = sync_ch.filter_irrelevant_ch_columns(test_dict)

    assert set(result.keys()) > set(settings.CH_RELEVANT_FIELDS)
    assert result['incorporation_date'] == date(1999, 3, 12)


def test_unzip_and_csv_read_on_the_fly():
    """Test on-the-fly extract."""
    fixture_loc = path.join(path.dirname(__file__), 'fixtures', 'CH_data_test.zip')

    with open(fixture_loc, 'rb') as f:
        with sync_ch.open_ch_zipped_csv(f) as csv_reader:
            result = list(csv_reader)

            assert len(result) == 5


@pytest.mark.django_db
@mock.patch('datahub.company.management.commands.sync_ch.stream_to_file_pointer', mock.MagicMock())
@mock.patch('datahub.company.management.commands.sync_ch.get_ch_latest_dump_file_list')
def test_full_ch_sync(file_list_mock):
    """Test the whole process."""
    CompaniesHouseCompanyFactory(company_number='08209948', name='Will change')
    file_list_mock.return_value = ['irrelevant']
    fixture_loc = path.join(path.dirname(__file__), 'fixtures', 'CH_data_test.zip')

    sync_ch.sync_ch(tmp_file_creator=lambda: open(fixture_loc, 'rb'))

    assert CompaniesHouseCompany.objects.count() == 4
    assert CompaniesHouseCompany.objects.get(company_number='08209948').name == '! LTD'
