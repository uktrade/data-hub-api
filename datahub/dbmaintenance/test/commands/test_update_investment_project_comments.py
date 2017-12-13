from io import BytesIO

import pytest
from django.core.management import call_command

from datahub.investment.test.factories import InvestmentProjectFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber):
    """Test that the command updates the relevant records ignoring ones with errors."""
    investment_projects = [
        # investment project in CSV doesn't exist so row should fail

        # comment should get updated
        InvestmentProjectFactory(),
        # should be ignored
        InvestmentProjectFactory(),
    ]

    old_description = investment_projects[1].description

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""Id,comments
00000000-0000-0000-0000-000000000000,Comment 1
{investment_projects[0].id},Comment 2
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

    call_command('update_investment_project_comments', bucket, object_key)

    for investment_project in investment_projects:
        investment_project.refresh_from_db()

    assert investment_projects[0].description == 'Comment 2'
    assert investment_projects[1].description == old_description


def test_simulate(s3_stubber):
    """Test that the command only simulates the actions if --simulate is passed in."""
    investment_projects = InvestmentProjectFactory.create_batch(2)
    old_descriptions = [ip.description for ip in investment_projects]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""Id,comments
{investment_projects[0].id},Comment 1
{investment_projects[1].id},Comment 2
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

    call_command('update_investment_project_comments', bucket, object_key, simulate=True)

    for investment_project in investment_projects:
        investment_project.refresh_from_db()

    assert investment_projects[0].description == old_descriptions[0]
    assert investment_projects[1].description == old_descriptions[1]
