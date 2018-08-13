from datetime import datetime
from io import BytesIO

import pytest
from django.core.management import call_command
from django.utils.timezone import utc
from reversion.models import Version

from datahub.investment.test.factories import InvestmentProjectFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber):
    """Test that the command updates the relevant records ignoring ones with errors."""
    investment_projects = [
        # investment project in CSV doesn't exist so row should fail

        # created_on should get updated
        InvestmentProjectFactory(),
        # should be ignored
        InvestmentProjectFactory(),
        # date in the file is invalid so it should fail
        InvestmentProjectFactory(),
    ]

    created_on_dates = [ip.created_on for ip in investment_projects]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,createdon
00000000-0000-0000-0000-000000000000,2016-09-29 14:03:20.000
{investment_projects[0].id},2015-09-29 11:03:20.000
{investment_projects[2].id},invalid_date
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

    call_command('update_investment_project_created_on', bucket, object_key)

    for investment_project in investment_projects:
        investment_project.refresh_from_db()

    assert investment_projects[0].created_on == datetime(2015, 9, 29, 11, 3, 20, tzinfo=utc)
    assert investment_projects[1].created_on == created_on_dates[1]
    assert investment_projects[2].created_on == created_on_dates[2]


def test_simulate(s3_stubber):
    """Test that the command only simulates the actions if --simulate is passed in."""
    investment_projects = InvestmentProjectFactory.create_batch(2)
    created_on_dates = [ip.created_on for ip in investment_projects]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,createdon
{investment_projects[0].id},2015-09-29 11:03:20.000
{investment_projects[1].id},2015-09-29 11:03:20.000
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

    call_command('update_investment_project_created_on', bucket, object_key, simulate=True)

    for investment_project in investment_projects:
        investment_project.refresh_from_db()

    assert investment_projects[0].created_on == created_on_dates[0]
    assert investment_projects[1].created_on == created_on_dates[1]


def test_audit_log(s3_stubber):
    """Test that the audit log is being created."""
    investment_project = InvestmentProjectFactory()

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,createdon
{investment_project.id},2015-09-29 11:03:20.000
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

    call_command('update_investment_project_created_on', bucket, object_key)

    investment_project.refresh_from_db()

    assert investment_project.created_on == datetime(2015, 9, 29, 11, 3, 20, tzinfo=utc)

    versions = Version.objects.get_for_object(investment_project)
    assert len(versions) == 1
    assert versions[0].revision.get_comment() == 'Created On migration.'
