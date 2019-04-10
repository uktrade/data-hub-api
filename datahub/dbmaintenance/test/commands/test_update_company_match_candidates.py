import json
from base64 import b64encode
from io import BytesIO

import pytest
from django.core.management import call_command

from datahub.company.test.factories import CompanyFactory
from datahub.dnb_match.models import DnBMatchingCSVRecord

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('WARNING')

    companies, data = _get_test_companies_and_data()

    wrong_json = b64encode('{"what": }'.encode('utf-8')).decode('utf-8')

    # to check that existing match will be overwritten
    company_2_match = DnBMatchingCSVRecord.objects.create(
        company_id=companies[2].id,
        batch_number=1,
        data=[],
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,data
00000000-0000-0000-0000-000000000000,NULL
{companies[0].id},{data[0]}
{companies[1].id},{wrong_json}
{companies[2].id},{data[0]}
{companies[3].id},invalidbase64
{companies[4].id},{data[1]}
{companies[5].id},{data[2]}
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content.encode(encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command('update_company_match_candidates', bucket, object_key, batch_number=1)

    assert 'Company matching query does not exist' in caplog.text
    assert 'json.decoder.JSONDecodeError' in caplog.text
    assert 'binascii.Error: Invalid base64-encoded string' in caplog.text
    assert 'Required fields are missing for given company' in caplog.text
    assert 'Could not resolve country for given company' in caplog.text
    assert len(caplog.records) == 5

    matches = DnBMatchingCSVRecord.objects.filter(
        company_id__in=(company.id for company in companies),
    )
    assert matches.count() == 2

    for match in matches:
        assert match.data == [
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
                'address_country': {
                    'id': '81756b9a-5d95-e211-a939-e4115bead28a',
                    'name': 'United States',
                },
                'confidence': 10,
                'source': 'cats',
            },
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
                'address_country': {
                    'id': '81756b9a-5d95-e211-a939-e4115bead28a',
                    'name': 'United States',
                },
                'confidence': 10,
                'source': 'cats',
            },
        ]

    company_2_match.refresh_from_db()
    assert company_2_match.data == [
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
            'address_country': {
                'id': '81756b9a-5d95-e211-a939-e4115bead28a',
                'name': 'United States',
            },
            'confidence': 10,
            'source': 'cats',
        },
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
            'address_country': {
                'id': '81756b9a-5d95-e211-a939-e4115bead28a',
                'name': 'United States',
            },
            'confidence': 10,
            'source': 'cats',
        },
    ]


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('WARNING')

    companies, data = _get_test_companies_and_data()

    # to check that existing match will not be overwritten
    company_2_match = DnBMatchingCSVRecord.objects.create(
        company_id=companies[2].id,
        batch_number=1,
        data=[],
    )

    wrong_json = b64encode('{"what": }'.encode('utf-8')).decode('utf-8')

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,data
00000000-0000-0000-0000-000000000000,NULL
{companies[0].id},{data[0]}
{companies[1].id},{wrong_json}
{companies[2].id},{data[0]}
{companies[3].id},invalidbase64
{companies[4].id},{data[1]}
{companies[5].id},{data[2]}
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content.encode(encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command(
        'update_company_match_candidates',
        bucket,
        object_key,
        batch_number=1,
        simulate=True,
    )

    assert 'Company matching query does not exist' in caplog.text
    assert 'json.decoder.JSONDecodeError' in caplog.text
    assert 'binascii.Error: Invalid base64-encoded string' in caplog.text
    assert 'Required fields are missing for given company' in caplog.text
    assert 'Could not resolve country for given company' in caplog.text
    assert len(caplog.records) == 5

    num_matches = DnBMatchingCSVRecord.objects.filter(
        company_id__in=(company.id for company in companies),
    ).count()
    assert num_matches == 1

    company_2_match.refresh_from_db()
    assert company_2_match.data == []


def _get_data_for_company(country_name='USA'):
    return {
        'duns_number': 12345,
        'name': 'test name',
        'global_ultimate_duns_number': 12345,
        'global_ultimate_name': 'test name global',
        'global_ultimate_country': 'USA',
        'address_1': '1st LTD street',
        'address_2': '',
        'address_town': 'London',
        'address_postcode': 'SW1A 1AA',
        'address_country': country_name,
        'confidence': 10,
        'source': 'cats',
    }


def _encode_data(data):
    raw_data = json.dumps(data)
    base64_data = b64encode(raw_data.encode('utf-8')).decode('utf-8')
    return base64_data


def _get_test_companies_and_data():
    companies = CompanyFactory.create_batch(6)

    records = [_get_data_for_company(), _get_data_for_company()]
    base64_record = _encode_data(records)
    data = [base64_record]

    # missing fields record
    missing_fields_record = [{'name': 'missing company'}]
    missing_fields_base64_record = _encode_data(missing_fields_record)
    data.append(missing_fields_base64_record)

    # unknown country
    unknown_country_record = [_get_data_for_company('UNKNOWN COUNTRY')]
    unknown_country_base64_record = _encode_data(unknown_country_record)
    data.append(unknown_country_base64_record)

    return companies, data
