from datetime import datetime, timezone
from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from freezegun import freeze_time
from reversion.models import Version

from datahub.company.test.factories import CompanyFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')

    original_datetime = datetime(2017, 1, 1, tzinfo=timezone.utc)

    with freeze_time(original_datetime):
        company_numbers = ['123', '456', '466879', '', None]
        companies = CompanyFactory.create_batch(
            5,
            company_number=factory.Iterator(company_numbers),
        )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,company_number
00000000-0000-0000-0000-000000000000,123456
{companies[0].pk},012345
{companies[1].pk},456
{companies[2].pk},null
{companies[3].pk},087891
{companies[4].pk},087892
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content.encode(encoding='utf-8'))
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key
        }
    )

    with freeze_time('2018-11-11 00:00:00'):
        call_command('update_company_company_number', bucket, object_key)

    for company in companies:
        company.refresh_from_db()

    assert 'Company matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [company.company_number for company in companies] == [
        '012345', '456', '', '087891', '087892'
    ]
    assert all(company.modified_on == original_datetime for company in companies)


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    company_numbers = ['123', '456', '466879', '', None]
    companies = CompanyFactory.create_batch(
        5,
        company_number=factory.Iterator(company_numbers),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,company_number
00000000-0000-0000-0000-000000000000,123456
{companies[0].pk},012345
{companies[1].pk},456
{companies[2].pk},null
{companies[3].pk},087891
{companies[4].pk},087892
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content.encode(encoding='utf-8'))
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key
        }
    )

    call_command('update_company_company_number', bucket, object_key, simulate=True)

    for company in companies:
        company.refresh_from_db()

    assert 'Company matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [company.company_number for company in companies] == company_numbers


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    company_without_change = CompanyFactory(
        company_number='132589',
    )
    company_with_change = CompanyFactory(
        company_number='566489',
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,company_number
{company_without_change.pk},132589
{company_with_change.pk},0566489
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content.encode(encoding='utf-8'))
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key
        }
    )

    call_command('update_company_company_number', bucket, object_key)

    versions = Version.objects.get_for_object(company_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(company_with_change)
    assert versions.count() == 1
    assert versions[0].revision.comment == 'Company number updated.'
