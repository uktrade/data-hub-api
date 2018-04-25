from io import BytesIO

import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.company.test.factories import CompanyFactory
from datahub.core.constants import HeadquarterType

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """
    Test that the command updates the specified records.

    Ignores ones with global hq already assigned or with errors.
    """
    caplog.set_level('ERROR')
    global_hq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ghq.value.id,
        global_headquarters=None,
    )
    other_global_hq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ghq.value.id,
        global_headquarters=None
    )

    company_needs_global_hq = CompanyFactory(
        global_headquarters=None
    )
    company_should_keep_current_global_hq = CompanyFactory(
        global_headquarters=other_global_hq
    )
    company_should_also_keep_global_hq = CompanyFactory(
        global_headquarters=other_global_hq
    )

    companies = [
        global_hq,
        other_global_hq,
        company_needs_global_hq,
        company_should_keep_current_global_hq,
        company_should_also_keep_global_hq,
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,global_hq_id
00000000-0000-0000-0000-000000000000,NULL
{company_needs_global_hq.id},{global_hq.id}
{company_should_keep_current_global_hq.id},{global_hq.id}
{company_should_also_keep_global_hq.id},NULL
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
    assert 'Company matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert company_needs_global_hq.global_headquarters == global_hq
    # Should not be updated
    assert company_should_keep_current_global_hq.global_headquarters == other_global_hq
    assert company_should_also_keep_global_hq.global_headquarters == other_global_hq


def test_overwrite(s3_stubber, caplog):
    """
    Test that the command updates all specified records (ignoring ones with errors).
    """
    caplog.set_level('ERROR')
    global_hq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ghq.value.id,
        global_headquarters=None
    )
    other_global_hq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ghq.value.id,
        global_headquarters=None
    )

    company_needs_global_hq = CompanyFactory(
        global_headquarters=None
    )
    company_should_get_new_global_hq = CompanyFactory(
        global_headquarters=other_global_hq
    )
    company_should_have_global_hq_removed = CompanyFactory(
        global_headquarters=other_global_hq
    )

    companies = [
        global_hq,
        other_global_hq,
        company_needs_global_hq,
        company_should_get_new_global_hq,
        company_should_have_global_hq_removed,
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,global_hq_id
00000000-0000-0000-0000-000000000000,NULL
{company_needs_global_hq.id},{global_hq.id}
{company_should_get_new_global_hq.id},{global_hq.id}
{company_should_have_global_hq_removed.id},NULL
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

    call_command('update_company_global_hq', bucket, object_key, overwrite=True)

    for company in companies:
        company.refresh_from_db()

    # Missing from data, fail
    assert 'Company matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert company_needs_global_hq.global_headquarters == global_hq
    assert company_should_get_new_global_hq.global_headquarters == global_hq
    assert company_should_have_global_hq_removed.global_headquarters is None


@pytest.mark.parametrize(
    'overwrite',
    (True, False)
)
def test_simulate(s3_stubber, caplog, overwrite):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')
    global_hq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ghq.value.id,
        global_headquarters=None
    )
    other_global_hq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ghq.value.id,
        global_headquarters=None
    )

    company_needs_global_hq = CompanyFactory(
        global_headquarters=None
    )
    company_should_get_new_global_hq = CompanyFactory(
        global_headquarters=other_global_hq
    )
    company_should_have_global_hq_removed = CompanyFactory(
        global_headquarters=other_global_hq
    )

    companies = [
        global_hq,
        other_global_hq,
        company_needs_global_hq,
        company_should_get_new_global_hq,
        company_should_have_global_hq_removed,
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,global_hq_id
00000000-0000-0000-0000-000000000000,NULL
{company_needs_global_hq.id},{global_hq.id}
{company_should_get_new_global_hq.id},{global_hq.id}
{company_should_have_global_hq_removed.id},NULL
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

    call_command(
        'update_company_global_hq',
        bucket,
        object_key,
        simulate=True,
        overwrite=overwrite
    )

    for company in companies:
        company.refresh_from_db()

    # Missing from data, fail
    assert 'Company matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert company_needs_global_hq.global_headquarters is None
    assert company_should_get_new_global_hq.global_headquarters == other_global_hq
    assert company_should_have_global_hq_removed.global_headquarters == other_global_hq


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    company_ghq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ghq.value.id,
        global_headquarters=None
    )
    company_needs_global_hq = CompanyFactory(
        global_headquarters=None
    )
    # Should not change
    company_ghq_set_already = CompanyFactory(
        global_headquarters=company_ghq
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,global_hq_id
{company_needs_global_hq.id},{company_ghq.id}
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
    assert len(versions) == 1
    assert versions[0].revision.comment == 'Global HQ data correction.'

    versions = Version.objects.get_for_object(company_ghq_set_already)
    assert len(versions) == 0


def test_override_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    company_ghq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ghq.value.id,
        global_headquarters=None
    )
    company_needs_global_hq = CompanyFactory(
        global_headquarters=None
    )
    company_ghq_set_already = CompanyFactory(
        global_headquarters=company_ghq
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,global_hq_id
{company_needs_global_hq.id},{company_ghq.id}
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

    call_command('update_company_global_hq', bucket, object_key, overwrite=True)

    versions = Version.objects.get_for_object(company_needs_global_hq)
    assert len(versions) == 1
    assert versions[0].revision.comment == 'Global HQ data correction.'

    versions = Version.objects.get_for_object(company_ghq_set_already)
    assert len(versions) == 1
    assert versions[0].revision.comment == 'Global HQ data correction.'


def test_validation(s3_stubber, caplog):
    """Test that data is being validated."""
    caplog.set_level('ERROR')
    not_a_global_hq = CompanyFactory(
        global_headquarters=None,
    )
    valid_global_hq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ghq.value.id,
        global_headquarters=None
    )
    other_valid_global_hq = CompanyFactory(
        headquarter_type_id=HeadquarterType.ghq.value.id,
        global_headquarters=None
    )

    company_needs_global_hq = CompanyFactory(
        global_headquarters=None
    )

    companies = [
        not_a_global_hq,
        valid_global_hq,
        other_valid_global_hq,
        company_needs_global_hq,
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,global_hq_id
00000000-0000-0000-0000-000000000000,NULL
{company_needs_global_hq.id},{not_a_global_hq.id}
{valid_global_hq.id},{other_valid_global_hq.id}
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

    assert 'Company matching query does not exist' in caplog.text

    invalid_ghq = 'Company to be linked as global headquarters must be a global headquarters.'
    assert invalid_ghq in caplog.text

    subsidiary_error = 'A company cannot both be and have a global headquarters'
    assert subsidiary_error in caplog.text

    assert len(caplog.records) == 3
