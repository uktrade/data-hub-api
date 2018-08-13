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

    company_no_hq_type = CompanyFactory(
        headquarter_type_id=None
    )
    company_ghq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ghq.value.id
    )
    company_ukhq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ukhq.value.id
    )
    company_ehq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ehq.value.id
    )
    companies = [
        company_no_hq_type,
        company_ghq,
        company_ukhq,
        company_ehq,
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,headquarter_type_id
00000000-0000-0000-0000-000000000000,NULL
{company_no_hq_type.id},{HeadquarterType.ehq.value.id}
{company_ghq.id},{HeadquarterType.ehq.value.id}
{company_ehq.id},{HeadquarterType.ehq.value.id}
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

    call_command('update_company_headquarter_type', bucket, object_key)

    for company in companies:
        company.refresh_from_db()

    assert 'Company matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert company_no_hq_type.headquarter_type_id == UUID(HeadquarterType.ehq.value.id)
    assert company_ghq.headquarter_type_id == UUID(HeadquarterType.ehq.value.id)
    assert company_ehq.headquarter_type_id == UUID(HeadquarterType.ehq.value.id)
    assert company_ukhq.headquarter_type_id == UUID(HeadquarterType.ukhq.value.id)


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    company_no_hq_type = CompanyFactory(
        headquarter_type_id=None
    )
    company_ghq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ghq.value.id
    )
    company_ukhq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ukhq.value.id
    )
    company_ehq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ehq.value.id
    )
    companies = [
        company_no_hq_type,
        company_ghq,
        company_ukhq,
        company_ehq,
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,headquarter_type_id
00000000-0000-0000-0000-000000000000,NULL
{company_no_hq_type.id},{HeadquarterType.ehq.value.id}
{company_ghq.id},{HeadquarterType.ehq.value.id}
{company_ehq.id},{HeadquarterType.ehq.value.id}
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

    call_command('update_company_headquarter_type', bucket, object_key, simulate=True)

    for company in companies:
        company.refresh_from_db()

    assert 'Company matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert company_no_hq_type.headquarter_type_id is None
    assert company_ghq.headquarter_type_id == UUID(HeadquarterType.ghq.value.id)
    assert company_ehq.headquarter_type_id == UUID(HeadquarterType.ehq.value.id)
    assert company_ukhq.headquarter_type_id == UUID(HeadquarterType.ukhq.value.id)


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    company_no_hq_type = CompanyFactory(
        headquarter_type_id=None
    )
    company_ehq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ehq.value.id
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,headquarter_type_id
{company_no_hq_type.id},{HeadquarterType.ehq.value.id}
{company_ehq.id},{HeadquarterType.ehq.value.id}
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

    call_command('update_company_headquarter_type', bucket, object_key)

    versions = Version.objects.get_for_object(company_no_hq_type)
    assert len(versions) == 1
    assert versions[0].revision.get_comment() == 'Headquarter type data migration correction.'

    versions = Version.objects.get_for_object(company_ehq)
    assert len(versions) == 0
