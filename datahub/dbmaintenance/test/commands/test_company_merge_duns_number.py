from io import BytesIO

import pytest
import reversion
from django.core.management import call_command

from datahub.company.test.factories import CompanyFactory

pytestmark = pytest.mark.django_db


def test_merge_id_duns_number(s3_stubber):
    """
    Test that the command merge id and duns number
    """
    with reversion.create_revision():
        company_1 = CompanyFactory(duns_number='123456789')
        company_2 = CompanyFactory(duns_number='223456789')
        company_3 = CompanyFactory(transferred_to=None)
        company_4 = CompanyFactory(transferred_to=None)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = (
        'id,duns\n'
        f'{company_3.id},{company_1.duns_number}\n'
        f'{company_4.id},{company_2.duns_number}\n'
    )

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
        'company_merge_duns_number',
        bucket,
        object_key,
        simulate=False,
    )

    company_3.refresh_from_db()
    company_4.refresh_from_db()
    assert company_3.transferred_to == company_1
    assert company_4.transferred_to == company_2
