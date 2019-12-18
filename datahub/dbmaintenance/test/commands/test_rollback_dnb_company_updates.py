from io import BytesIO
from unittest import mock

import pytest
from django.core.management import call_command

from datahub.company.test.factories import CompanyFactory

pytestmark = pytest.mark.django_db


@mock.patch(
    'datahub.dbmaintenance.management.commands.rollback_dnb_company_updates.'
    'rollback_dnb_company_update',
)
def test_run(mocked_rollback_dnb_company_update, s3_stubber):
    """
    Test that the command calls the rollback utility for the specified records.
    """
    companies = [
        CompanyFactory(duns_number='123456789'),
        CompanyFactory(duns_number='223456789'),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id
00000000-0000-0000-0000-000000000000
{companies[0].id}
{companies[1].id}
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content, encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    update_descriptor = 'foobar'
    call_command(
        'rollback_dnb_company_updates',
        bucket,
        object_key,
        update_descriptor=update_descriptor,
    )

    for company in companies:
        mocked_rollback_dnb_company_update.assert_any_call(company, update_descriptor)


@mock.patch(
    'datahub.dbmaintenance.management.commands.rollback_dnb_company_updates.'
    'rollback_dnb_company_update',
)
def test_simulate(mocked_rollback_dnb_company_update, s3_stubber):
    """
    Test that the command simulates rollbacks if --simulate is passed in.
    """
    companies = [
        CompanyFactory(duns_number='123456789'),
        CompanyFactory(duns_number='223456789'),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id
00000000-0000-0000-0000-000000000000
{companies[0].id}
{companies[1].id}
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content, encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command(
        'rollback_dnb_company_updates',
        bucket,
        object_key,
        update_descriptor='foobar',
        simulate=True,
    )

    assert not mocked_rollback_dnb_company_update.called
