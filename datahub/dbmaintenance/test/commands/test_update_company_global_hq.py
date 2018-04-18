from io import BytesIO
from uuid import UUID

import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.company.test.factories import CompanyFactory
from datahub.core.constants import HeadquarterType

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')

    company_needs_global_hq = CompanyFactory(
        global_headquarters=None
    )
    company_to_be_global_hq = CompanyFactory(
        global_headquarters=None
    )
    company_ghq_for_test = CompanyFactory(
        global_headquarters=None
    )
    company_ghq_set_already = CompanyFactory(
        global_headquarters = company_ghq_for_test
    )

    companies = [
        company_needs_global_hq,
        company_to_be_global_hq,
        company_ghq_for_test,
        company_ghq_set_already,
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,global_hq_id
00000000-0000-0000-0000-000000000000,NULL
{company_needs_global_hq.id},{company_to_be_global_hq.id}
{company_to_be_global_hq.id},NULL
{company_ghq_set_already.id},{company_to_be_global_hq.id}
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

    call_command('update_company_global_hq', bucket, object_key)

    for company in companies:
        company.refresh_from_db()

    # Missing from data, fail
    print("***** ***** ***** HUH", caplog.text)
    assert 'Company matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert company_needs_global_hq.global_headquarters == company_to_be_global_hq
    assert company_to_be_global_hq.global_headquarters == None
    # Should not be updated
    assert company_ghq_set_already.global_headquarters == company_ghq_for_test


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    company_needs_global_hq = CompanyFactory(
        global_headquarters=None
    )
    company_to_be_global_hq = CompanyFactory(
        global_headquarters=None
    )
    company_ghq_for_test = CompanyFactory(
        global_headquarters=None
    )
    company_ghq_set_already = CompanyFactory(
        global_headquarters = company_ghq_for_test
    )

    companies = [
        company_needs_global_hq,
        company_to_be_global_hq,
        company_ghq_for_test,
        company_ghq_set_already,
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,global_hq_id
00000000-0000-0000-0000-000000000000,NULL
{company_needs_global_hq.id},{company_to_be_global_hq.id}
{company_to_be_global_hq.id},NULL
{company_ghq_set_already.id},{company_to_be_global_hq.id}
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

    call_command('update_company_global_hq', bucket, object_key, simulate=True)

    for company in companies:
        company.refresh_from_db()

    # Missing from data, fail
    assert 'Company matching query does not exist' in caplog.text
    assert len(caplog.records) == 1


    assert company_needs_global_hq.global_headquarters == None
    assert company_to_be_global_hq.global_headquarters == None
    # Should not be updated
    assert company_ghq_set_already.global_headquarters == company_ghq_for_test


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    company_needs_global_hq = CompanyFactory(
        global_headquarters=None
    )
    company_ghq_for_test = CompanyFactory(
        global_headquarters=None
    )
    # Should not change
    company_ghq_set_already = CompanyFactory(
        global_headquarters = company_ghq_for_test
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,global_hq_id
{company_needs_global_hq.id},{company_to_be_global_hq.id}
{company_ghq_set_already.id},NULL
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

    call_command('update_company_global_hq', bucket, object_key)

    versions = Version.objects.get_for_object(company_needs_global_hq)
    for v in versions:
        print(v)
    assert len(versions) == 1
    assert versions[0].revision.comment == 'Global HQ data migration.'

    print(company_ghq_set_already.global_headquarters)
    versions = Version.objects.get_for_object(company_ghq_set_already)
    for v in versions:
        print(v)
    assert len(versions) == 0
