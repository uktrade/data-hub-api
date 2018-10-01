from io import BytesIO

import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.metadata.models import UKRegion

pytestmark = pytest.mark.django_db


def test_run(s3_stubber, caplog):
    """Test that the command updates the specified records (ignoring ones with errors)."""
    caplog.set_level('ERROR')

    regions = list(UKRegion.objects.all())

    investment_projects = [
        InvestmentProjectFactory(actual_uk_regions=[]),
        InvestmentProjectFactory(actual_uk_regions=[]),
        InvestmentProjectFactory(actual_uk_regions=regions[0:1]),
        InvestmentProjectFactory(actual_uk_regions=regions[1:2]),
        InvestmentProjectFactory(actual_uk_regions=[]),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,actual_uk_regions
00000000-0000-0000-0000-000000000000,
{investment_projects[0].pk},
{investment_projects[1].pk},{regions[2].pk}
{investment_projects[2].pk},"{regions[3].pk},{regions[4].pk}"
{investment_projects[3].pk},
{investment_projects[4].pk},"{regions[3].pk},{regions[4].pk}"
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

    call_command('update_investment_project_actual_uk_regions', bucket, object_key)

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [list(project.actual_uk_regions.all()) for project in investment_projects] == [
        [], regions[2:3], regions[0:1], regions[1:2], regions[3:5],
    ]


def test_simulate(s3_stubber, caplog):
    """Test that the command simulates updates if --simulate is passed in."""
    caplog.set_level('ERROR')

    regions = list(UKRegion.objects.all())

    investment_projects = [
        InvestmentProjectFactory(actual_uk_regions=[]),
        InvestmentProjectFactory(actual_uk_regions=[]),
        InvestmentProjectFactory(actual_uk_regions=regions[0:1]),
        InvestmentProjectFactory(actual_uk_regions=regions[1:2]),
        InvestmentProjectFactory(actual_uk_regions=[]),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,actual_uk_regions
00000000-0000-0000-0000-000000000000,
{investment_projects[0].pk},invalid-uuid
{investment_projects[1].pk},{regions[2].pk}
{investment_projects[2].pk},"{regions[3].pk},{regions[4].pk}"
{investment_projects[3].pk},
{investment_projects[4].pk},"{regions[3].pk},{regions[4].pk}"
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

    call_command('update_investment_project_actual_uk_regions', bucket, object_key, simulate=True)

    for project in investment_projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert '"invalid-uuid" is not a valid UUID.' in caplog.text
    assert len(caplog.records) == 2

    assert [list(project.actual_uk_regions.all()) for project in investment_projects] == [
        [], [], regions[0:1], regions[1:2], [],
    ]


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    regions = list(UKRegion.objects.all())

    project_with_change = InvestmentProjectFactory(actual_uk_regions=[])
    project_without_change = InvestmentProjectFactory(actual_uk_regions=regions[0:1])

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,actual_uk_regions
{project_with_change.pk},{regions[2].pk}
{project_without_change.pk},{regions[2].pk}
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

    call_command('update_investment_project_actual_uk_regions', bucket, object_key)

    versions = Version.objects.get_for_object(project_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(project_with_change)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'Actual UK regions migration.'
