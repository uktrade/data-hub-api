from io import BytesIO

import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import SectorFactory

pytestmark = pytest.mark.django_db


def test_run(s3_stubber):
    """Test that the command updates the relevant records ignoring ones with errors."""
    sectors = SectorFactory.create_batch(5)

    investment_projects = [
        # investment project in CSV doesn't exist so row should fail

        # sector should get updated
        InvestmentProjectFactory(sector_id=sectors[0].id),
        # sector should get updated
        InvestmentProjectFactory(sector_id=None),
        # sector should not get updated
        InvestmentProjectFactory(sector_id=None),
        # should be ignored
        InvestmentProjectFactory(sector_id=sectors[3].id),
        # should be skipped because of an error
        InvestmentProjectFactory(sector_id=sectors[4].id),
    ]

    new_sectors = SectorFactory.create_batch(5)

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_sector,new_sector
00000000-0000-0000-0000-000000000000,NULL,NULL
{investment_projects[0].id},{sectors[0].id},{new_sectors[0].id}
{investment_projects[1].id},NULL,{new_sectors[1].id}
{investment_projects[2].id},{new_sectors[2].id},{new_sectors[2].id}
{investment_projects[4].id},invalid_id,another_invalid_id
"""

    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content, encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command('update_investment_project_sector', bucket, object_key)

    for investment_project in investment_projects:
        investment_project.refresh_from_db()

    assert investment_projects[0].sector == new_sectors[0]
    assert investment_projects[1].sector == new_sectors[1]
    assert investment_projects[2].sector is None
    assert investment_projects[3].sector == sectors[3]
    assert investment_projects[4].sector == sectors[4]


def test_simulate(s3_stubber):
    """Test that the command only simulates the actions if --simulate is passed in."""
    new_sectors = SectorFactory.create_batch(5)
    investment_projects = InvestmentProjectFactory.create_batch(2)
    old_sectors = [ip.sector for ip in investment_projects]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_sector,new_sector
{investment_projects[0].id},{old_sectors[0].id},{new_sectors[0].id}
{investment_projects[1].id},{old_sectors[1].id},{new_sectors[1].id}
"""
    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content, encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command('update_investment_project_sector', bucket, object_key, simulate=True)

    for investment_project in investment_projects:
        investment_project.refresh_from_db()

    assert investment_projects[0].sector == old_sectors[0]
    assert investment_projects[1].sector == old_sectors[1]


def test_audit_log(s3_stubber):
    """Test that audit log is being created."""
    new_sector = SectorFactory()
    investment_project = InvestmentProjectFactory()
    old_sector = investment_project.sector

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_sector,new_sector
{investment_project.id},{old_sector.id},{new_sector.id}
"""
    s3_stubber.add_response(
        'get_object',
        {
            'Body': BytesIO(bytes(csv_content, encoding='utf-8')),
        },
        expected_params={
            'Bucket': bucket,
            'Key': object_key,
        },
    )

    call_command('update_investment_project_sector', bucket, object_key)

    investment_project.refresh_from_db()

    assert investment_project.sector == new_sector
    versions = Version.objects.get_for_object(investment_project)
    assert len(versions) == 1
    assert versions[0].revision.get_comment() == 'Sector migration.'
