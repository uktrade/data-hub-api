from io import BytesIO

import pytest
from django.core.management import call_command

from datahub.company.test.factories import AdviserFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber):
    """Test that the command updates the relevant records ignoring ones with errors."""
    advisers = [
        # order in CSV doesn't exist so row should fail

        # region should get updated
        AdviserFactory(telephone_number='000000000'),
        # region should get updated
        AdviserFactory(telephone_number='111111111'),
        # should be ignored
        AdviserFactory(telephone_number='111'),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,telephone_number
00000000-0000-0000-0000-000000000000,123
{advisers[0].id},+441234567890
{advisers[1].id},+440987654321
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content, encoding='utf-8'))
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key
        }
    )

    call_command('update_adviser_telephone_number', bucket, object_key)

    for adviser in advisers:
        adviser.refresh_from_db()

    assert advisers[0].telephone_number == '+441234567890'
    assert advisers[1].telephone_number == '+440987654321'
    assert advisers[2].telephone_number == '111'


def test_simulate(s3_stubber):
    """Test that the command only simulates the actions if --simulate is passed in."""
    advisers = [
        AdviserFactory(telephone_number='000000000'),
        AdviserFactory(telephone_number='111111111'),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,telephone_number
{advisers[0].id},+441234567890
{advisers[1].id},+440987654321
    """
    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content, encoding='utf-8'))
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key
        }
    )

    call_command('update_adviser_telephone_number', bucket, object_key, simulate=True)

    for adviser in advisers:
        adviser.refresh_from_db()

    assert advisers[0].telephone_number == '000000000'
    assert advisers[1].telephone_number == '111111111'
