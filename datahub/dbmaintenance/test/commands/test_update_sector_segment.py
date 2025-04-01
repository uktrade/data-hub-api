from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.metadata.test.factories import SectorFactory

pytestmark = pytest.mark.django_db


def test_happy_path(s3_stubber):
    """Test that the command updates the specified records."""
    old_sectors = ['sector_1_old', 'sector_2_old', 'sector_3_old']
    new_sectors = ['sector_1_new', 'sector_2_new', 'sector_3_new']

    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(old_sectors),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_sector_segment,new_sector_segment
{sectors[0].pk},{old_sectors[0]},{new_sectors[0]}
{sectors[1].pk},{old_sectors[1]},{new_sectors[1]}
{sectors[2].pk},{old_sectors[2]},{new_sectors[2]}
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

    call_command('update_sector_segment', bucket, object_key)

    for sector in sectors:
        sector.refresh_from_db()

    assert [sector.segment for sector in sectors] == new_sectors


def test_non_existent_sector(s3_stubber, caplog):
    """Test that the command logs an error when PK does not exist."""
    caplog.set_level('ERROR')

    old_sectors = ['sector_1_old', 'sector_2_old', 'sector_3_old']
    new_sectors = ['sector_1_new', 'sector_2_new', 'sector_3_new']

    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(old_sectors),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_sector_segment,new_sector_segment
{sectors[0].pk},{old_sectors[0]},{new_sectors[0]}
00000000-0000-0000-0000-000000000000,{old_sectors[1]},{new_sectors[1]}
{sectors[2].pk},{old_sectors[2]},{new_sectors[2]}
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

    call_command('update_sector_segment', bucket, object_key)

    for sector in sectors:
        sector.refresh_from_db()

    assert 'Sector matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [sector.segment for sector in sectors] == [
        new_sectors[0],
        old_sectors[1],
        new_sectors[2],
    ]


def test_no_change(s3_stubber, caplog):
    """Test that the command ignores records that haven't changed
    or records with incorrect current values.
    """
    caplog.set_level('WARNING')

    old_sectors = ['sector_1_old', 'sector_2_old', 'sector_3_old']
    new_sectors = ['sector_1_new', 'sector_2_new', 'sector_3_new']

    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(old_sectors),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_sector_segment,new_sector_segment
{sectors[0].pk},{old_sectors[0]},{new_sectors[0]}
{sectors[1].pk},{old_sectors[1]},{old_sectors[1]}
{sectors[2].pk},bla,{new_sectors[2]}
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

    call_command('update_sector_segment', bucket, object_key)

    for sector in sectors:
        sector.refresh_from_db()

    assert f'Not updating sector {sectors[1]} as its segment has not changed' in caplog.text
    assert f'Not updating sector {sectors[2]} as its segment has not changed' in caplog.text
    assert len(caplog.records) == 2

    assert [sector.segment for sector in sectors] == [
        new_sectors[0],
        old_sectors[1],
        old_sectors[2],
    ]


def test_simulate(s3_stubber):
    """Test that the command simulates updates if --simulate is passed in."""
    old_sectors = ['sector_1_old', 'sector_2_old', 'sector_3_old']
    new_sectors = ['sector_1_new', 'sector_2_new', 'sector_3_new']

    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(old_sectors),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_sector_segment,new_sector_segment
{sectors[0].pk},{old_sectors[0]},{new_sectors[0]}
{sectors[1].pk},{old_sectors[1]},{new_sectors[1]}
{sectors[2].pk},{old_sectors[2]},{new_sectors[2]}
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

    call_command('update_sector_segment', bucket, object_key, simulate=True)

    for sector in sectors:
        sector.refresh_from_db()

    assert [sector.segment for sector in sectors] == old_sectors


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    sector_without_change = SectorFactory(
        segment='sector_1',
    )
    sector_with_change = SectorFactory(
        segment='sector_2',
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_sector_segment,new_sector_segment
{sector_without_change.pk},{sector_without_change.segment},{sector_without_change.segment}
{sector_with_change.pk},{sector_with_change.segment},sector_new
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

    call_command('update_sector_segment', bucket, object_key)

    versions = Version.objects.get_for_object(sector_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(sector_with_change)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'Sector segment correction.'
