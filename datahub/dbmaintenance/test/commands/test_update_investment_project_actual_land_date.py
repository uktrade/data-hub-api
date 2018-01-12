from datetime import date
from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.core.constants import InvestmentProjectStage
from datahub.investment.test.factories import InvestmentProjectFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('WARNING')

    stages = [
        InvestmentProjectStage.prospect.value.id,
        InvestmentProjectStage.assign_pm.value.id,
        InvestmentProjectStage.active.value.id,
        InvestmentProjectStage.verify_win.value.id,
        InvestmentProjectStage.won.value.id,  # won projects should not be updated
    ]
    old_dates = [date(2016, 2, 20), None, date(2013, 6, 13), date(2016, 8, 23), date(2016, 8, 23)]
    investment_projects = InvestmentProjectFactory.create_batch(
        5,
        stage_id=factory.Iterator(stages),
        actual_land_date=factory.Iterator(old_dates)
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_actual_land_date,new_actual_land_date
00000000-0000-0000-0000-000000000000,2016-01-20,null
{investment_projects[0].pk},2016-02-20,null
{investment_projects[1].pk},2016-02-28,2016-03-28
{investment_projects[2].pk},2013-06-13,
{investment_projects[3].pk},2016-08-23,2016-08-24
{investment_projects[4].pk},2016-08-23,2016-08-24
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

    call_command('update_investment_project_actual_land_date', bucket, object_key)

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert 'Not updating project in Won stage' in caplog.text
    assert len(caplog.records) == 2

    assert [project.actual_land_date for project in investment_projects] == [
        None, None, None, date(2016, 8, 24), date(2016, 8, 23)
    ]


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    old_dates = [date(2016, 2, 20), None, date(2013, 6, 13), date(2016, 8, 23)]
    investment_projects = InvestmentProjectFactory.create_batch(
        4, actual_land_date=factory.Iterator(old_dates)
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_actual_land_date,new_actual_land_date
00000000-0000-0000-0000-000000000000,2016-01-20,null
{investment_projects[0].pk},2016-02-20,null
{investment_projects[1].pk},2016-02-28,2016-03-28
{investment_projects[2].pk},2013-06-13,
{investment_projects[3].pk},2016-08-23,2016-08-24
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

    call_command('update_investment_project_actual_land_date', bucket, object_key, simulate=True)

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [project.actual_land_date for project in investment_projects] == old_dates


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    project_without_change = InvestmentProjectFactory(actual_land_date=date(2017, 2, 2))
    project_with_change = InvestmentProjectFactory(actual_land_date=date(2017, 2, 2))

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_actual_land_date,new_actual_land_date
{project_without_change.pk},2017-02-24,
{project_with_change.pk},2017-02-02,2016-08-24
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

    call_command('update_investment_project_actual_land_date', bucket, object_key)

    versions = Version.objects.get_for_object(project_without_change)
    assert len(versions) == 0

    versions = Version.objects.get_for_object(project_with_change)
    assert len(versions) == 1
    assert versions[0].revision.comment == 'Actual land date migration correction.'
