from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import SectorFactory

pytestmark = pytest.mark.django_db


def test_happy_path(s3_stubber):
    """Test that the command updates the specified records."""
    old_sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1_old', 'sector_2_old', 'sector_3_old']),
    )

    projects = InvestmentProjectFactory.create_batch(
        3,
        sector_id=factory.Iterator([sector.pk for sector in old_sectors]),
    )

    new_sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1_new', 'sector_2_new', 'sector_3_new']),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_sector_id,new_sector_id
{projects[0].pk},{old_sectors[0].pk},{new_sectors[0].pk}
{projects[1].pk},{old_sectors[1].pk},{new_sectors[1].pk}
{projects[2].pk},{old_sectors[2].pk},{new_sectors[2].pk}
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

    call_command('update_investment_project_sector_disabled_signals', bucket, object_key)

    for project in projects:
        project.refresh_from_db()

    assert [project.sector for project in projects] == new_sectors


def test_non_existent_project(s3_stubber, caplog):
    """Test that the command logs an error when the investment project PK does not exist."""
    caplog.set_level('ERROR')

    old_sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1_old', 'sector_2_old', 'sector_3_old']),
    )

    projects = InvestmentProjectFactory.create_batch(
        3,
        sector_id=factory.Iterator([sector.pk for sector in old_sectors]),
    )

    new_sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1_new', 'sector_2_new', 'sector_3_new']),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_sector_id,new_sector_id
{projects[0].pk},{old_sectors[0].pk},{new_sectors[0].pk}
{projects[1].pk},{old_sectors[1].pk},{new_sectors[1].pk}
00000000-0000-0000-0000-000000000000,{old_sectors[2].pk},{new_sectors[2].pk}
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

    call_command('update_investment_project_sector_disabled_signals', bucket, object_key)

    for project in projects:
        project.refresh_from_db()

    assert 'InvestmentProject matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [project.sector for project in projects] == [
        new_sectors[0],
        new_sectors[1],
        old_sectors[2],
    ]


def test_non_existent_sector(s3_stubber, caplog):
    """Test that the command logs an error when the sector PK does not exist."""
    caplog.set_level('ERROR')

    old_sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1_old', 'sector_2_old', 'sector_3_old']),
    )

    projects = InvestmentProjectFactory.create_batch(
        3,
        sector_id=factory.Iterator([sector.pk for sector in old_sectors]),
    )

    new_sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1_new', 'sector_2_new', 'sector_3_new']),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_sector_id,new_sector_id
{projects[0].pk},{old_sectors[0].pk},{new_sectors[0].pk}
{projects[1].pk},{old_sectors[1].pk},{new_sectors[1].pk}
{projects[2].pk},{old_sectors[2].pk},00000000-0000-0000-0000-000000000000
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

    call_command('update_investment_project_sector_disabled_signals', bucket, object_key)

    for project in projects:
        project.refresh_from_db()

    assert 'Sector matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [project.sector for project in projects] == [
        new_sectors[0],
        new_sectors[1],
        old_sectors[2],
    ]


def test_no_change(s3_stubber, caplog):
    """Test that the command ignores records that haven't changed
    or records with incorrect current values.
    """
    caplog.set_level('WARNING')

    old_sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1_old', 'sector_2_old', 'sector_3_old']),
    )

    projects = InvestmentProjectFactory.create_batch(
        3,
        sector_id=factory.Iterator([sector.pk for sector in old_sectors]),
    )

    new_sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1_new', 'sector_2_new', 'sector_3_new']),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_sector_id,new_sector_id
{projects[0].pk},{old_sectors[0].pk},{new_sectors[0].pk}
{projects[1].pk},{old_sectors[1].pk},{old_sectors[1].pk}
{projects[2].pk},00000000-0000-0000-0000-000000000000,{new_sectors[2].pk}
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

    call_command('update_investment_project_sector_disabled_signals', bucket, object_key)

    for project in projects:
        project.refresh_from_db()

    assert (
        f'Not updating InvestmentProject {projects[1]} as its sector has not changed'
    ) in caplog.text
    assert (
        f'Not updating InvestmentProject {projects[2]} as its sector has not changed'
    ) in caplog.text
    assert len(caplog.records) == 2

    assert [project.sector for project in projects] == [
        new_sectors[0],
        old_sectors[1],
        old_sectors[2],
    ]


def test_simulate(s3_stubber):
    """Test that the command simulates updates if --simulate is passed in."""
    old_sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1_old', 'sector_2_old', 'sector_3_old']),
    )

    projects = InvestmentProjectFactory.create_batch(
        3,
        sector_id=factory.Iterator([sector.pk for sector in old_sectors]),
    )

    new_sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1_new', 'sector_2_new', 'sector_3_new']),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_sector_id,new_sector_id
{projects[0].pk},{old_sectors[0].pk},{new_sectors[0].pk}
{projects[1].pk},{old_sectors[1].pk},{new_sectors[1].pk}
{projects[2].pk},{old_sectors[2].pk},{new_sectors[2].pk}
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
        'update_investment_project_sector_disabled_signals',
        bucket,
        object_key,
        simulate=True,
    )

    for project in projects:
        project.refresh_from_db()

    assert [project.sector for project in projects] == old_sectors


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1', 'sector_2', 'sector_3']),
    )

    project_without_change = InvestmentProjectFactory(
        sector_id=sectors[0].pk,
    )

    project_with_change = InvestmentProjectFactory(
        sector_id=sectors[1].pk,
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_sector_id,new_sector_id
{project_without_change.pk},{sectors[0].pk},{sectors[0].pk}
{project_with_change.pk},{sectors[1].pk},{sectors[2].pk}
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

    call_command('update_investment_project_sector_disabled_signals', bucket, object_key)

    versions = Version.objects.get_for_object(project_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(project_with_change)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'InvestmentProject sector correction.'
