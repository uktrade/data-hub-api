from datetime import datetime, timezone
from io import BytesIO
from unittest import mock

import factory
import pytest
from django.core.management import call_command
from freezegun import freeze_time
from reversion.models import Version

from datahub.company.test.factories import CompanyFactory, DuplicateCompanyFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')

    original_datetime = datetime(2017, 1, 1, tzinfo=timezone.utc)

    with freeze_time(original_datetime):
        duns_numbers = ['123', '456', '466879', '777', None]
        companies = CompanyFactory.create_batch(
            5,
            duns_number=factory.Iterator(duns_numbers),
        )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,duns_number
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
            'Body': BytesIO(csv_content.encode(encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    with freeze_time('2018-11-11 00:00:00'):
        call_command('update_company_duns_number', bucket, object_key)

    for company in companies:
        company.refresh_from_db()

    assert 'Company matching query does not exist' in caplog.text

    assert all(company.modified_on == original_datetime for company in companies)
    assert [company.duns_number for company in companies] == [
        '012345',
        '456',
        None,
        '087891',
        '087892',
    ]


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    duns_numbers = ['123', '456', '466879', '777', None]
    companies = CompanyFactory.create_batch(
        5,
        duns_number=factory.Iterator(duns_numbers),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,duns_number
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
            'Body': BytesIO(csv_content.encode(encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command('update_company_duns_number', bucket, object_key, simulate=True)

    for company in companies:
        company.refresh_from_db()

    assert 'Company matching query does not exist' in caplog.text

    assert [company.duns_number for company in companies] == duns_numbers


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    company_without_change = CompanyFactory(
        duns_number='132589',
    )
    company_with_change = CompanyFactory(
        duns_number='566489',
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,duns_number
{company_without_change.pk},132589
{company_with_change.pk},0566489
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

    call_command('update_company_duns_number', bucket, object_key)

    versions = Version.objects.get_for_object(company_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(company_with_change)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'Duns number updated.'


def test_companies_which_already_have_the_target_duns_are_logged(s3_stubber, caplog):
    """Tests log contains company error for company which already has duns"""
    caplog.set_level('INFO')
    company_with_duns = CompanyFactory(
        duns_number='132589',
    )
    company_without_duns = CompanyFactory()

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,duns_number
{company_without_duns.id},{company_with_duns.duns_number}
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

    call_command('update_company_duns_number', bucket, object_key)

    assert 'Errors:' in caplog.text
    assert (
        'Cannot assign duns number to company as another company already has this duns number. '
    ) in caplog.text
    assert f'Company with duns already: {company_with_duns.id}' in caplog.text


def test_companies_which_are_already_merged_into_target_are_logged(s3_stubber, caplog):
    """
    Tests log contains error if the source company has already been merged into a company which
    has the target duns number.
    """
    caplog.set_level('INFO')
    company_with_duns = CompanyFactory(
        duns_number='132589',
    )
    company_already_merged = DuplicateCompanyFactory(transferred_to=company_with_duns)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,duns_number
{company_already_merged.id},{company_with_duns.duns_number}
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

    call_command('update_company_duns_number', bucket, object_key)

    assert (
        'Total companies already merged with company matching target duns so not updated: 1'
    ) in caplog.text


def test_companies_which_are_already_merged_but_not_into_target_are_logged(s3_stubber, caplog):
    """
    Tests log contains error if the source company has already been merged into another company.
    """
    caplog.set_level('INFO')
    company_with_duns = CompanyFactory(
        duns_number='132589',
    )
    company_already_merged = DuplicateCompanyFactory(transferred_to=CompanyFactory())

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,duns_number
{company_already_merged.id},{company_with_duns.duns_number}
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

    call_command('update_company_duns_number', bucket, object_key)

    assert (
        'Total companies already merged and marked as duplicates so not updated: 1'
    ) in caplog.text


@mock.patch(
    'datahub.dbmaintenance.management.commands.update_company_duns_number.Command'
    '.is_duns_already_assigned_to_another_company',
)
def test_unexpected_errors_are_logged(
    mocked_func,
    s3_stubber,
    caplog,
):
    """
    Tests log contains error if the source company has already been merged into another company.
    """
    mocked_func.return_value = False
    caplog.set_level('INFO')
    company_with_duns = CompanyFactory(
        duns_number='132589',
    )
    company_without_duns = CompanyFactory()

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,duns_number
{company_without_duns.id},{company_with_duns.duns_number}
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

    call_command('update_company_duns_number', bucket, object_key)

    assert 'IntegrityError' in caplog.text
    assert 'duplicate key value violates unique constraint' in caplog.text
    assert f'Key (duns_number)=({company_with_duns.duns_number}) already exists' in caplog.text
