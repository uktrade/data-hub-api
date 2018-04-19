from io import BytesIO

import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.core.constants import InvestmentProjectStage
from uuid import UUID


pytestmark = pytest.mark.django_db


def test_run(s3_stubber):
    """Test that the command updates the relevant records ignoring ones with errors."""

    investment_projects = [
        # stage should get updated
        InvestmentProjectFactory(stage_id=InvestmentProjectStage.prospect.value.id),
        # stage has been updated so shouldn't change
        InvestmentProjectFactory(stage_id=InvestmentProjectStage.active.value.id),
        # should be moved back
        InvestmentProjectFactory(stage_id=InvestmentProjectStage.won.value.id),
    ]

    new_stages = [InvestmentProjectStage.assign_pm, InvestmentProjectStage.active, InvestmentProjectStage.verify_win]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_stage,new_stage
{investment_projects[0].id},{investment_projects[0].stage_id},{new_stages[0].value.id}
{investment_projects[1].id},{investment_projects[1].stage_id},{new_stages[1].value.id}
{investment_projects[2].id},{investment_projects[2].stage_id},{new_stages[2].value.id}
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

    call_command('update_investment_project_stage', bucket, object_key)

    for investment_project in investment_projects:
        investment_project.refresh_from_db()

    assert investment_projects[0].stage_id == (UUID(new_stages[0].value.id))
    assert investment_projects[1].stage_id == (UUID(new_stages[1].value.id))
    assert investment_projects[2].stage_id == (UUID(new_stages[2].value.id))


def test_simulate(s3_stubber):
    """Test that the command only simulates the actions if --simulate is passed in."""
    investment_projects = InvestmentProjectFactory.create_batch(2)
    old_stages = [ip.stage for ip in investment_projects]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_stage,new_stage
{investment_projects[0].id},{old_stages[0].id},{InvestmentProjectStage.prospect.value.id}
{investment_projects[1].id},{old_stages[1].id},{InvestmentProjectStage.won.value.id}
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

    call_command('update_investment_project_stage', bucket, object_key, simulate=True)

    for investment_project in investment_projects:
        investment_project.refresh_from_db()

    assert investment_projects[0].stage == old_stages[0]
    assert investment_projects[1].stage == old_stages[1]


def test_audit_log(s3_stubber):
    """Test that audit log is being created."""
    new_stage = InvestmentProjectStage.won
    investment_project = InvestmentProjectFactory()
    old_stage = investment_project.stage

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_stage,new_stage
{investment_project.id},{old_stage.id},{new_stage.value.id}
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

    call_command('update_investment_project_stage', bucket, object_key)

    investment_project.refresh_from_db()

    versions = Version.objects.get_for_object(investment_project)
    assert len(versions) == 1
    assert versions[0].revision.comment == 'Stage migration.'
