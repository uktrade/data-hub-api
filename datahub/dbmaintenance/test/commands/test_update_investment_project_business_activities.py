from io import BytesIO

import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.metadata.models import InvestmentBusinessActivity

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """
    Test that the command updates the specified records, checking if current business activities
    match the old business activities in the CSV.
    """
    caplog.set_level('ERROR')

    business_activities = list(InvestmentBusinessActivity.objects.all())
    old_business_activities = [[], [], business_activities[0:2], business_activities[2:3]]
    investment_projects = InvestmentProjectFactory.create_batch(4)

    for project, project_business_activities in zip(investment_projects, old_business_activities):
        project.business_activities.set(project_business_activities)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_business_activities,new_business_activities
00000000-0000-0000-0000-000000000000,null,null
{investment_projects[0].pk},null,null
{investment_projects[1].pk},null,{business_activities[2].pk}
{investment_projects[2].pk},"{business_activities[0].pk},{business_activities[1].pk}","{business_activities[0].pk},{business_activities[1].pk}"
{investment_projects[3].pk},{business_activities[5].pk},"{business_activities[0].pk},{business_activities[1].pk},{business_activities[2].pk},{business_activities[3].pk}"
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content.encode(encoding='utf-8'))
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        }
    )

    call_command('update_investment_project_business_activities', bucket, object_key)

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [list(project.business_activities.all()) for project in investment_projects] == [
        [],
        business_activities[2:3],
        business_activities[0:2],
        business_activities[2:3],  # Old business activities did not match
    ]


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    business_activities = list(InvestmentBusinessActivity.objects.all())
    old_business_activities = [[], [], business_activities[0:2], business_activities[2:3]]
    investment_projects = InvestmentProjectFactory.create_batch(4)

    for project, project_business_activities in zip(investment_projects, old_business_activities):
        project.business_activities.set(project_business_activities)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_business_activities,new_business_activities
00000000-0000-0000-0000-000000000000,null,null
{investment_projects[0].pk},null,null
{investment_projects[1].pk},null,{business_activities[2].pk}
{investment_projects[2].pk},"{business_activities[0].pk},{business_activities[1].pk}","{business_activities[0].pk},{business_activities[1].pk}"
{investment_projects[3].pk},{business_activities[5].pk},"{business_activities[0].pk},{business_activities[1].pk},{business_activities[2].pk},{business_activities[3].pk}"
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content.encode(encoding='utf-8'))
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        }
    )

    call_command(
        'update_investment_project_business_activities',
        bucket,
        object_key,
        simulate=True,
    )

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [list(project.business_activities.all())
            for project in investment_projects] == old_business_activities


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    business_activities = list(InvestmentBusinessActivity.objects.all())

    project_without_change = InvestmentProjectFactory(business_activities=business_activities[0:1])
    project_with_change = InvestmentProjectFactory(business_activities=[])
    project_already_updated = InvestmentProjectFactory(
        business_activities=business_activities[0:1]
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_business_activities,new_business_activities
{project_without_change.pk},{business_activities[1].pk},{business_activities[0].pk}
{project_with_change.pk},null,{business_activities[2].pk}
{project_already_updated.pk},{business_activities[0].pk},{business_activities[0].pk}
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(csv_content.encode(encoding='utf-8'))
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        }
    )

    call_command('update_investment_project_business_activities', bucket, object_key)

    versions = Version.objects.get_for_object(project_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(project_already_updated)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(project_with_change)
    assert versions.count() == 1
    assert versions[0].revision.comment == 'Business activities data migration correction.'
