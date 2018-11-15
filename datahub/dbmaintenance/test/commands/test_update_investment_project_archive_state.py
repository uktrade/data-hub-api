from io import BytesIO

import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.company.test.factories import AdviserFactory
from datahub.investment.models import InvestmentProject
from datahub.investment.test.factories import InvestmentProjectFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def investment_projects_and_csv_content():
    """Prepare archived investment projects and csv content."""
    investment_projects = InvestmentProjectFactory.create_batch(
        6,
        status=InvestmentProject.STATUSES.ongoing,
    )

    for project in investment_projects:
        project.archive(user=AdviserFactory())

    csv_content = f"""id,Action Required
00000000-0000-0000-0000-000000000000,
{investment_projects[0].pk},
{investment_projects[1].pk},"Unarchive, change status to Abandoned"
{investment_projects[2].pk},"Unarchive, change status to Lost"
{investment_projects[3].pk},"Unarchive, change status to Dormant"
{investment_projects[4].pk},"Unarchive, change status to Whatever"
{investment_projects[5].pk},"Unarchive, change status to Delayed"
"""
    yield (investment_projects, csv_content)


def test_run(s3_stubber, caplog, investment_projects_and_csv_content):
    """
    Test that the command updates the specified records
    (ignoring ones with errors and warnings).
    """
    caplog.set_level('WARNING')

    investment_projects, csv_content = investment_projects_and_csv_content

    bucket = 'test_bucket'
    object_key = 'test_key'

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

    call_command('update_investment_project_archived_state', bucket, object_key)

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert (
        f'Not updating project {investment_projects[0].pk} '
        f'as its desired status could not be derived from [].'
    ) in caplog.text
    assert (
        f'Not updating project {investment_projects[4].pk} '
        f'as its desired status could not be derived from '
        f'[Unarchive, change status to Whatever].'
    ) in caplog.text
    assert len(caplog.records) == 3

    assert [(project.archived, project.status) for project in investment_projects] == [
        (True, InvestmentProject.STATUSES.ongoing),     # not updated
        (False, InvestmentProject.STATUSES.abandoned),
        (False, InvestmentProject.STATUSES.lost),
        (False, InvestmentProject.STATUSES.dormant),
        (True, InvestmentProject.STATUSES.ongoing),     # not updated
        (False, InvestmentProject.STATUSES.delayed),
    ]


def test_simulate(s3_stubber, caplog, investment_projects_and_csv_content):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('WARNING')

    investment_projects, csv_content = investment_projects_and_csv_content

    bucket = 'test_bucket'
    object_key = 'test_key'

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

    call_command('update_investment_project_archived_state', bucket, object_key, simulate=True)

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert (
        f'Not updating project {investment_projects[0].pk} '
        f'as its desired status could not be derived from [].'
    ) in caplog.text
    assert (
        f'Not updating project {investment_projects[4].pk} '
        f'as its desired status could not be derived from '
        f'[Unarchive, change status to Whatever].'
    ) in caplog.text
    assert len(caplog.records) == 3

    assert [(project.archived, project.status) for project in investment_projects] == [
        (True, InvestmentProject.STATUSES.ongoing),
        (True, InvestmentProject.STATUSES.ongoing),
        (True, InvestmentProject.STATUSES.ongoing),
        (True, InvestmentProject.STATUSES.ongoing),
        (True, InvestmentProject.STATUSES.ongoing),
        (True, InvestmentProject.STATUSES.ongoing),
    ]


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    project_with_change = InvestmentProjectFactory(status=InvestmentProject.STATUSES.ongoing)
    project_with_change.archive(user=AdviserFactory())
    project_without_change = InvestmentProjectFactory(status=InvestmentProject.STATUSES.abandoned)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,Action Required
{project_with_change.pk},"Unarchive, change status to Abandoned"
{project_without_change.pk},"Unarchive, change status to Abandoned"
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

    call_command('update_investment_project_archived_state', bucket, object_key)

    versions = Version.objects.get_for_object(project_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(project_with_change)
    assert versions.count() == 1
    comment = versions[0].revision.get_comment()
    assert comment == 'Investment Project was unarchived and has changed its status.'
