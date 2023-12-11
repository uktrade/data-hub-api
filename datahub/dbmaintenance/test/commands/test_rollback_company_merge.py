from io import BytesIO

import pytest
import reversion
from django.core.management import call_command

from datahub.company.merge_company import merge_companies
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import create_test_user

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, formatted_dnb_company):
    """
    Test that the command successfully rolls back the specified records.
    """
    with reversion.create_revision():
        company_1 = CompanyFactory(duns_number='123456789')
        company_2 = CompanyFactory(duns_number='223456789')
        company_3 = CompanyFactory(transferred_to=None)
        company_4 = CompanyFactory(transferred_to=None)

    user = create_test_user()
    merge_companies(company_3, company_1, user)
    merge_companies(company_4, company_2, user)

    company_3.refresh_from_db()
    company_4.refresh_from_db()
    assert company_3.transferred_to == company_1
    assert company_4.transferred_to == company_2

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f'id\n{company_3.id}\n{company_4.id}'

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
        'rollback_company_merge',
        bucket,
        object_key,
    )

    company_3.refresh_from_db()
    company_4.refresh_from_db()
    assert company_3.transferred_to is None
    assert company_4.transferred_to is None


def test_simulate(s3_stubber):
    """
    Test that the command simulates rollbacks if --simulate is passed in.
    """
    with reversion.create_revision():
        company_1 = CompanyFactory(duns_number='123456789')
        company_2 = CompanyFactory(duns_number='223456789')
        company_3 = CompanyFactory(transferred_to=None)
        company_4 = CompanyFactory(transferred_to=None)

    user = create_test_user()
    merge_companies(company_3, company_1, user)
    merge_companies(company_4, company_2, user)

    company_3.refresh_from_db()
    company_4.refresh_from_db()
    assert company_3.transferred_to == company_1
    assert company_4.transferred_to == company_2

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f'id\n{company_3.id}\n{company_4.id}'

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
        'rollback_company_merge',
        bucket,
        object_key,
        simulate=True,
    )

    company_3.refresh_from_db()
    company_4.refresh_from_db()
    assert company_3.transferred_to == company_1
    assert company_4.transferred_to == company_2
