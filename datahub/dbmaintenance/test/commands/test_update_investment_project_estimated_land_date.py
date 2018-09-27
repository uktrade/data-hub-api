from datetime import date
from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.investment.test.factories import InvestmentProjectFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')

    allow_blank_estimated_land_date = [False, False, True, True]
    estimated_land_date = [date(2016, 2, 20), None, None, date(2016, 8, 23)]
    investment_projects = InvestmentProjectFactory.create_batch(
        4,
        allow_blank_estimated_land_date=factory.Iterator(allow_blank_estimated_land_date),
        estimated_land_date=factory.Iterator(estimated_land_date),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,allow_blank_estimated_land_date,estimated_land_date
00000000-0000-0000-0000-000000000000,true,null
{investment_projects[0].pk},true,null
{investment_projects[1].pk},false,2018-01-01
{investment_projects[2].pk},false,2017-01-05
{investment_projects[3].pk},true,2016-08-23
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

    call_command('update_investment_project_estimated_land_date', bucket, object_key)

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [project.allow_blank_estimated_land_date for project in investment_projects] == [
        True, False, False, True,
    ]
    assert [project.estimated_land_date for project in investment_projects] == [
        None, date(2018, 1, 1), date(2017, 1, 5), date(2016, 8, 23),
    ]


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    allow_blank_estimated_land_date = [False, False, True, True]
    estimated_land_date = [date(2016, 2, 20), None, None, date(2016, 8, 23)]
    investment_projects = InvestmentProjectFactory.create_batch(
        4,
        allow_blank_estimated_land_date=factory.Iterator(allow_blank_estimated_land_date),
        estimated_land_date=factory.Iterator(estimated_land_date),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,allow_blank_estimated_land_date,estimated_land_date
00000000-0000-0000-0000-000000000000,true,null
{investment_projects[0].pk},true,null
{investment_projects[1].pk},false,2018-01-01
{investment_projects[2].pk},False,2017-01-05
{investment_projects[3].pk},TRUE,2016-08-23
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

    call_command(
        'update_investment_project_estimated_land_date', bucket, object_key, simulate=True,
    )

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [project.allow_blank_estimated_land_date
            for project in investment_projects] == allow_blank_estimated_land_date
    assert [project.estimated_land_date for project in investment_projects] == estimated_land_date


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    project_without_change = InvestmentProjectFactory(
        allow_blank_estimated_land_date=True,
        estimated_land_date=date(2017, 5, 2),
    )
    project_with_change = InvestmentProjectFactory(
        allow_blank_estimated_land_date=False,
        estimated_land_date=date(2017, 2, 2),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,allow_blank_estimated_land_date,estimated_land_date
{project_without_change.pk},true,2017-05-02
{project_with_change.pk},true,2017-05-05
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

    call_command('update_investment_project_estimated_land_date', bucket, object_key)

    versions = Version.objects.get_for_object(project_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(project_with_change)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'Estimated land date migration correction.'
