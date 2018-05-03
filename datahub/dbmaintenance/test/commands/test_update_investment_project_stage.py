from io import BytesIO
from uuid import UUID

import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.company.test.factories import AdviserFactory
from datahub.core.constants import InvestmentProjectStage
from datahub.investment.test.factories import InvestmentProjectFactory


pytestmark = pytest.mark.django_db


def test_run_without_user(s3_stubber):
    """Test that the command updates the relevant records ignoring ones with errors."""
    investment_projects = [
        # stage should get updated 'forwards' in the investment flow
        InvestmentProjectFactory(stage_id=InvestmentProjectStage.prospect.value.id),
        # Shouldn't be changed - stages match
        InvestmentProjectFactory(stage_id=InvestmentProjectStage.active.value.id),
        # should be moved back
        InvestmentProjectFactory(stage_id=InvestmentProjectStage.won.value.id),
    ]

    new_stages = [
        InvestmentProjectStage.assign_pm,
        InvestmentProjectStage.active,
        InvestmentProjectStage.verify_win
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""investment_project_id,stage_id
{investment_projects[0].id},{new_stages[0].value.id}
{investment_projects[1].id},{new_stages[1].value.id}
{investment_projects[2].id},{new_stages[2].value.id}
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

    assert investment_projects[0].modified_by is None
    assert investment_projects[0].stage_id == (UUID(new_stages[0].value.id))
    assert investment_projects[1].modified_by is None
    assert investment_projects[1].stage_id == (UUID(new_stages[1].value.id))
    assert investment_projects[2].modified_by is None
    assert investment_projects[2].stage_id == (UUID(new_stages[2].value.id))


def test_run_with_user(s3_stubber):
    """Test that the command updates the relevant records ignoring ones with errors."""
    new_adviser = AdviserFactory()
    investment_projects = [
        # stage should get updated
        InvestmentProjectFactory(stage_id=InvestmentProjectStage.prospect.value.id,
                                 modified_by=AdviserFactory()),
        # Shouldn't be changed - stages match
        InvestmentProjectFactory(stage_id=InvestmentProjectStage.active.value.id,
                                 modified_by=AdviserFactory()),
        # should be moved back
        InvestmentProjectFactory(stage_id=InvestmentProjectStage.won.value.id,
                                 modified_by=AdviserFactory()),
    ]

    new_stages = [
        InvestmentProjectStage.assign_pm,
        InvestmentProjectStage.active,
        InvestmentProjectStage.verify_win
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""investment_project_id,stage_id
{investment_projects[0].id},{new_stages[0].value.id}
{investment_projects[1].id},{new_stages[1].value.id}
{investment_projects[2].id},{new_stages[2].value.id}
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
    # set an explicit adviser id to make the changes
    call_command('update_investment_project_stage',
                 bucket, object_key,
                 modified_by=str(new_adviser.id))

    for investment_project in investment_projects:
        investment_project.refresh_from_db()

    # Adviser should change to reflect the command's user
    assert investment_projects[0].modified_by == new_adviser
    assert investment_projects[0].stage_id == (UUID(new_stages[0].value.id))
    assert investment_projects[1].modified_by == new_adviser
    assert investment_projects[1].stage_id == (UUID(new_stages[1].value.id))
    assert investment_projects[2].modified_by == new_adviser
    assert investment_projects[2].stage_id == (UUID(new_stages[2].value.id))


def test_simulate(s3_stubber):
    """Test that the command only simulates the actions if --simulate is passed in."""
    investment_projects = InvestmentProjectFactory.create_batch(2)
    old_stages = [ip.stage for ip in investment_projects]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""investment_project_id,stage_id
{investment_projects[0].id},{InvestmentProjectStage.prospect.value.id}
{investment_projects[1].id},{InvestmentProjectStage.won.value.id}
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
    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""investment_project_id,stage_id
{investment_project.id},{new_stage.value.id}
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
    assert versions[0].revision.comment == 'Stage correction.'
