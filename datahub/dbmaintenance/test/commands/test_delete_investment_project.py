from io import BytesIO

import pytest
from django.core.management import call_command

from datahub.cleanup.query_utils import get_relations_to_delete
from datahub.investment.models import InvestmentProject
from datahub.investment.test.factories import InvestmentProjectFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def investment_projects_and_csv_content():
    """Get investment projects and CSV content."""
    investment_projects = InvestmentProjectFactory.create_batch(3)

    csv_content = f"""id
00000000-0000-0000-0000-000000000000
{investment_projects[0].id}
{investment_projects[2].id}
"""
    yield (investment_projects, csv_content.encode('utf-8'))


def test_run(s3_stubber, caplog, investment_projects_and_csv_content):
    """Test that the command deletes investment projects."""
    caplog.set_level('ERROR')

    investment_projects, csv_content = investment_projects_and_csv_content

    bucket = 'test_bucket'
    object_key = 'test_key'

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content)),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command('delete_investment_project', bucket, object_key)

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    deleted_projects = (investment_projects[0], investment_projects[2])
    for investment_project in deleted_projects:
        with pytest.raises(InvestmentProject.DoesNotExist):
            investment_project.refresh_from_db()

    investment_projects[1].refresh_from_db()
    assert investment_projects[1].id is not None


def test_simulate(s3_stubber, caplog, investment_projects_and_csv_content):
    """Test that the command only simulates the actions if --simulate is passed in."""
    caplog.set_level('INFO')

    investment_projects, csv_content = investment_projects_and_csv_content

    bucket = 'test_bucket'
    object_key = 'test_key'

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content)),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    # Calculate the number of records to be deleted just for one investment project. Three projects
    # tested have the same number of related records so it is enough to calculate just for one.
    # 1 for the investment project itself plus related records
    records_to_be_deleted = 1
    relations_to_delete = get_relations_to_delete(InvestmentProject)
    for related in relations_to_delete:
        related_model = related.related_model
        related_qs = related_model._base_manager.filter(
            **{related.field.name: investment_projects[0].id},
        )
        related_qs_count = related_qs.count()
        records_to_be_deleted += related_qs_count

    call_command('delete_investment_project', bucket, object_key, simulate=True)

    # In the test, two investment projects should be deleted
    assert caplog.text.count(
        f'{records_to_be_deleted} records deleted for investment project: ',
    ) == 2
    assert 'InvestmentProject matching query does not exist' in caplog.text

    for investment_project in investment_projects:
        investment_project.refresh_from_db()
        assert investment_project.id is not None
