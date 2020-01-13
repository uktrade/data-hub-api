from io import BytesIO
from unittest import mock

import pytest
import reversion
from django.core.management import call_command
from reversion.models import Version

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.dnb_api.constants import ALL_DNB_UPDATED_MODEL_FIELDS
from datahub.dnb_api.utils import update_company_from_dnb


pytestmark = pytest.mark.django_db


def test_run(s3_stubber, formatted_dnb_company):
    """
    Test that the command successfully rolls back the specified records.
    """
    with reversion.create_revision():
        companies = [
            CompanyFactory(duns_number='123456789'),
            CompanyFactory(duns_number='223456789'),
        ]

    original_companies = {company.id: Company.objects.get(id=company.id) for company in companies}

    update_descriptor = 'foobar'
    # Simulate updating the companies from DNB, which sets a revision with the specified
    # update descriptor
    for company in companies:
        formatted_dnb_company['duns_number'] = company.duns_number
        update_company_from_dnb(
            company,
            formatted_dnb_company,
            update_descriptor=update_descriptor,
        )

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
        update_descriptor=update_descriptor,
    )

    # Ensure that the companies are reverted to their previous versions
    for company in companies:
        company.refresh_from_db()
        for field in ALL_DNB_UPDATED_MODEL_FIELDS:
            assert getattr(company, field) == getattr(original_companies[company.id], field)

        latest_version = Version.objects.get_for_object(company)[0]
        assert latest_version.revision.comment == f'Reverted D&B update from: {update_descriptor}'


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
