from datetime import datetime, timezone
from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from freezegun import freeze_time
from reversion.models import Version

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')

    original_datetime = datetime(2017, 1, 1, tzinfo=timezone.utc)

    with freeze_time(original_datetime):
        export_potential_scores = [
            Company.EXPORT_POTENTIAL_SCORES.very_high,
            Company.EXPORT_POTENTIAL_SCORES.medium,
            Company.EXPORT_POTENTIAL_SCORES.low,
            Company.EXPORT_POTENTIAL_SCORES.very_high,
            Company.EXPORT_POTENTIAL_SCORES.high,
        ]
        companies = CompanyFactory.create_batch(
            5,
            export_potential=factory.Iterator(export_potential_scores),
        )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""datahub_company_id,export_propensity
00000000-0000-0000-0000-000000000000,Low
{companies[0].pk},High
{companies[1].pk},Very high
{companies[2].pk},dummy
{companies[3].pk},High
{companies[4].pk},Very high
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

    with freeze_time('2018-11-11 00:00:00'):
        call_command('update_company_export_potential', bucket, object_key)

    for company in companies:
        company.refresh_from_db()

    assert 'Company matching query does not exist' in caplog.text
    assert "KeyError: \'dummy\'" in caplog.text
    assert len(caplog.records) == 2

    assert [company.export_potential for company in companies] == [
        Company.EXPORT_POTENTIAL_SCORES.high,
        Company.EXPORT_POTENTIAL_SCORES.very_high,
        Company.EXPORT_POTENTIAL_SCORES.low,
        Company.EXPORT_POTENTIAL_SCORES.high,
        Company.EXPORT_POTENTIAL_SCORES.very_high,
    ]
    assert all(company.modified_on == original_datetime for company in companies)


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    export_potential_scores = [
        Company.EXPORT_POTENTIAL_SCORES.very_high,
        Company.EXPORT_POTENTIAL_SCORES.medium,
        Company.EXPORT_POTENTIAL_SCORES.low,
        Company.EXPORT_POTENTIAL_SCORES.very_high,
        Company.EXPORT_POTENTIAL_SCORES.high,
    ]
    companies = CompanyFactory.create_batch(
        5,
        export_potential=factory.Iterator(export_potential_scores),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""datahub_company_id,export_propensity
00000000-0000-0000-0000-000000000000,Low
{companies[0].pk},High
{companies[1].pk},Very high
{companies[2].pk},Low
{companies[3].pk},High
{companies[4].pk},Very high
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

    call_command('update_company_export_potential', bucket, object_key, simulate=True)

    for company in companies:
        company.refresh_from_db()

    assert 'Company matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [company.export_potential for company in companies] == export_potential_scores


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    company_without_change = CompanyFactory(
        export_potential=Company.EXPORT_POTENTIAL_SCORES.high,
    )
    company_with_change = CompanyFactory(
        export_potential=Company.EXPORT_POTENTIAL_SCORES.medium,
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""datahub_company_id,export_propensity
{company_without_change.pk},High
{company_with_change.pk},Very high
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

    call_command('update_company_export_potential', bucket, object_key)

    company_without_change.refresh_from_db()
    assert company_without_change.export_potential == Company.EXPORT_POTENTIAL_SCORES.high
    versions = Version.objects.get_for_object(company_without_change)
    assert versions.count() == 0

    company_with_change.refresh_from_db()
    assert company_with_change.export_potential == Company.EXPORT_POTENTIAL_SCORES.very_high
    versions = Version.objects.get_for_object(company_with_change)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'Export potential updated.'
