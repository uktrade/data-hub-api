import json
from base64 import b64encode
from io import BytesIO

import pytest
from django.core.management import call_command

from datahub.company.test.factories import CompanyFactory
from datahub.dnb_match.models import DnBMatchingResult

pytestmark = pytest.mark.django_db


def _get_data_for_company(company_id):
    return {
        'company_id': str(company_id),
        'cats': {
            'like': ['napping', 'purring', 'hunting', 'eating'],
            'dislike': ['empty_bowl'],
            'confidence': 3,
        },
    }


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')

    companies = CompanyFactory.create_batch(4)
    data = []

    for company in companies:
        record = _get_data_for_company(company.id)
        raw_record = json.dumps(record)
        base64_record = b64encode(raw_record.encode('utf-8')).decode('utf-8')
        data.append(base64_record)

    wrong_json = b64encode('{"what": }'.encode('utf-8')).decode('utf-8')

    # to check that existing match will be overwritten
    company_2_match = DnBMatchingResult.objects.create(
        company_id=companies[2].id,
        data={'hello': 'world', 'confidence': 100},
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,data
00000000-0000-0000-0000-000000000000,NULL
{companies[0].id},{data[0]}
{companies[1].id},{wrong_json}
{companies[2].id},{data[2]}
{companies[3].id},invalidbase64
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

    call_command('update_company_matches', bucket, object_key)

    assert 'Company matching query does not exist' in caplog.text
    assert 'json.decoder.JSONDecodeError' in caplog.text
    assert 'binascii.Error: Invalid base64-encoded string' in caplog.text
    assert len(caplog.records) == 3

    matches = DnBMatchingResult.objects.filter(company__in=companies)
    assert matches.count() == 2

    for match in matches:
        assert match.data == _get_data_for_company(match.company_id)

    company_2_match.refresh_from_db()
    assert company_2_match.data == _get_data_for_company(company_2_match.company_id)


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    companies = CompanyFactory.create_batch(4)
    data = []

    for company in companies:
        record = _get_data_for_company(company.id)
        raw_record = json.dumps(record)
        base64_record = b64encode(raw_record.encode('utf-8')).decode('utf-8')
        data.append(base64_record)

    # to check that existing match will be overwritten
    company_2_match = DnBMatchingResult.objects.create(
        company_id=companies[2].id,
        data={'hello': 'world', 'confidence': 100},
    )

    wrong_json = b64encode('{"what": }'.encode('utf-8')).decode('utf-8')

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,data
00000000-0000-0000-0000-000000000000,NULL
{companies[0].id},{data[0]}
{companies[1].id},{wrong_json}
{companies[2].id},{data[2]}
{companies[3].id},invalidbase64
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

    call_command('update_company_matches', bucket, object_key, simulate=True)

    assert 'Company matching query does not exist' in caplog.text
    assert 'json.decoder.JSONDecodeError' in caplog.text
    assert 'binascii.Error: Invalid base64-encoded string' in caplog.text
    assert len(caplog.records) == 3

    num_matches = DnBMatchingResult.objects.filter(company__in=companies).count()
    assert num_matches == 1

    company_2_match.refresh_from_db()
    assert company_2_match.data == {'hello': 'world', 'confidence': 100}
