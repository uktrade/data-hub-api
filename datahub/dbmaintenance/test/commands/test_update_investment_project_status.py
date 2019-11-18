"""Tests for the update_investment_project_status management command."""

from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import InvestmentProjectFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('simulate', (True, False))
def test_run(s3_stubber, caplog, simulate):
    """
    Test that the command:

    - updates records if simulate=False
    - doesn't update records if simulate=True
    - ignores rows with errors
    """
    caplog.set_level('ERROR')

    original_statuses = [
        InvestmentProject.STATUSES.ongoing,
        InvestmentProject.STATUSES.ongoing,
        InvestmentProject.STATUSES.won,
        InvestmentProject.STATUSES.abandoned,
    ]
    investment_projects = InvestmentProjectFactory.create_batch(
        len(original_statuses),
        status=factory.Iterator(original_statuses),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,status
00000000-0000-0000-0000-000000000000,ongoing
{investment_projects[0].pk},invalid
{investment_projects[1].pk},ongoing
{investment_projects[2].pk},dormant
{investment_projects[3].pk},ongoing
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

    call_command('update_investment_project_status', bucket, object_key, simulate=simulate)

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert '"invalid" is not a valid choice.' in caplog.text
    assert len(caplog.records) == 2

    if simulate:
        assert [project.status for project in investment_projects] == original_statuses
    else:
        expected_statuses = [
            InvestmentProject.STATUSES.ongoing,  # no change as the new value wasn't valid
            InvestmentProject.STATUSES.ongoing,
            InvestmentProject.STATUSES.dormant,
            InvestmentProject.STATUSES.ongoing,
        ]
        assert [project.status for project in investment_projects] == expected_statuses


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created for updated rows."""
    project_without_change = InvestmentProjectFactory(status=InvestmentProject.STATUSES.ongoing)
    project_with_change = InvestmentProjectFactory(status=InvestmentProject.STATUSES.ongoing)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,status
{project_without_change.pk},ongoing
{project_with_change.pk},delayed
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

    call_command('update_investment_project_status', bucket, object_key)

    versions = Version.objects.get_for_object(project_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(project_with_change)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'Bulk status update.'
