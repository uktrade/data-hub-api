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
        profile_statuses = [
            Company.GreatProfileStatus.UNPUBLISHED,
            None,
            Company.GreatProfileStatus.PUBLISHED,
            Company.GreatProfileStatus.PUBLISHED,
            Company.GreatProfileStatus.UNPUBLISHED,
            Company.GreatProfileStatus.PUBLISHED,
        ]
        companies = CompanyFactory.create_batch(
            6,
            great_profile_status=factory.Iterator(profile_statuses),
        )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""datahub_company_id,is_published_find_a_supplier,has_find_a_supplier_profile
00000000-0000-0000-0000-000000000000,t,t
{companies[0].pk},t,t
{companies[1].pk},f,t
{companies[2].pk},f,f
{companies[3].pk},t,f
{companies[4].pk},f,t
{companies[5].pk},x,y
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
        call_command('update_company_great_profile_status', bucket, object_key)

    for company in companies:
        company.refresh_from_db()

    assert 'Company matching query does not exist' in caplog.text
    assert 'Must be a valid boolean' in caplog.text
    assert len(caplog.records) == 2

    assert [company.great_profile_status for company in companies] == [
        Company.GreatProfileStatus.PUBLISHED,
        Company.GreatProfileStatus.UNPUBLISHED,
        None,
        None,
        Company.GreatProfileStatus.UNPUBLISHED,
        Company.GreatProfileStatus.PUBLISHED,
    ]
    assert all(company.modified_on == original_datetime for company in companies)


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    profile_statuses = [
        Company.GreatProfileStatus.UNPUBLISHED,
        None,
        Company.GreatProfileStatus.PUBLISHED,
        Company.GreatProfileStatus.PUBLISHED,
        Company.GreatProfileStatus.UNPUBLISHED,
    ]
    companies = CompanyFactory.create_batch(
        5,
        great_profile_status=factory.Iterator(profile_statuses),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""datahub_company_id,is_published_find_a_supplier,has_find_a_supplier_profile
00000000-0000-0000-0000-000000000000,t,t
{companies[0].pk},t,t
{companies[1].pk},f,t
{companies[2].pk},f,f
{companies[3].pk},t,t
{companies[4].pk},f,t
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

    call_command('update_company_great_profile_status', bucket, object_key, simulate=True)

    for company in companies:
        company.refresh_from_db()

    assert 'Company matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [company.great_profile_status for company in companies] == profile_statuses


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    company_without_change = CompanyFactory(
        great_profile_status=Company.GreatProfileStatus.PUBLISHED,
    )
    company_with_change = CompanyFactory(
        great_profile_status=Company.GreatProfileStatus.UNPUBLISHED,
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""datahub_company_id,is_published_find_a_supplier,has_find_a_supplier_profile
{company_without_change.pk},t,t
{company_with_change.pk},t,t
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

    call_command('update_company_great_profile_status', bucket, object_key)

    company_without_change.refresh_from_db()
    assert company_without_change.great_profile_status == Company.GreatProfileStatus.PUBLISHED
    versions = Version.objects.get_for_object(company_without_change)
    assert versions.count() == 0

    company_with_change.refresh_from_db()
    assert company_with_change.great_profile_status == Company.GreatProfileStatus.PUBLISHED
    versions = Version.objects.get_for_object(company_with_change)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'GREAT profile status updated.'
