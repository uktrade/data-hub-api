from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.company.test.factories import CompanyFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')

    company_names = ('abc', 'def', 'ghi', 'jkl', 'mno')

    companies = CompanyFactory.create_batch(
        5,
        name=factory.Iterator(company_names),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_company_name,new_company_name
00000000-0000-0000-0000-000000000000,test,test
{companies[0].pk},{companies[0].name},xyz100
{companies[1].pk},{companies[1].name},xyz102
{companies[2].pk},what,xyz103
{companies[3].pk},{companies[3].name},xyz104
{companies[4].pk},{companies[4].name},xyz105
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

    call_command('update_company_name', bucket, object_key)

    for company in companies:
        company.refresh_from_db()

    assert 'Company matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [company.name for company in companies] == [
        'xyz100', 'xyz102', 'ghi', 'xyz104', 'xyz105',
    ]


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    company_names = ['abc', 'def', 'ghi', 'jkl', 'mno']

    companies = CompanyFactory.create_batch(
        5,
        name=factory.Iterator(company_names),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_company_name,new_company_name
00000000-0000-0000-0000-000000000000,test,test
{companies[0].pk},{companies[0].name},xyz100
{companies[1].pk},{companies[1].name},xyz102
{companies[2].pk},what,xyz103
{companies[3].pk},{companies[3].name},xyz104
{companies[4].pk},{companies[4].name},xyz105
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

    call_command('update_company_name', bucket, object_key, simulate=True)

    for company in companies:
        company.refresh_from_db()

    assert 'Company matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [company.name for company in companies] == company_names


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    company_without_change = CompanyFactory(
        name='132589',
    )
    company_with_change = CompanyFactory(
        name='566489',
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_company_name,new_company_name
{company_without_change.pk},132590,132589
{company_with_change.pk},566489,111665
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

    call_command('update_company_name', bucket, object_key)

    versions = Version.objects.get_for_object(company_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(company_with_change)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'Company name correction.'
