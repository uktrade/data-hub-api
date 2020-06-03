from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from django.utils.timezone import now
from reversion.models import Version

from datahub.metadata.test.factories import SectorFactory

pytestmark = pytest.mark.django_db


def test_happy_path(s3_stubber):
    """Test that the command disables the specified records."""
    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1', 'sector_2', 'sector_3']),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id
{sectors[0].pk}
{sectors[1].pk}
{sectors[2].pk}
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

    call_command('disable_sector', bucket, object_key)
    current_time = now()

    for sector in sectors:
        sector.refresh_from_db()

    assert all([sector.was_disabled_on(current_time) for sector in sectors])


def test_non_existent_sector(s3_stubber, caplog):
    """Test that the command logs an error when the sector PK does not exist."""
    caplog.set_level('ERROR')

    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1', 'sector_2', 'sector_3']),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id
{sectors[0].pk}
{sectors[1].pk}
00000000-0000-0000-0000-000000000000
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

    call_command('disable_sector', bucket, object_key)
    current_time = now()

    for sector in sectors:
        sector.refresh_from_db()

    assert 'Sector matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [sector.was_disabled_on(current_time) for sector in sectors] == [
        True, True, False,
    ]


def test_sector_with_children(s3_stubber, caplog):
    """Test that the command ignores records that have children."""
    caplog.set_level('WARNING')

    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1', 'sector_2', 'sector_3']),
    )

    # Attach a child to sector_3
    SectorFactory(
        segment='sector_3_child',
        parent=sectors[2],
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id
{sectors[0].pk}
{sectors[1].pk}
{sectors[2].pk}
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

    call_command('disable_sector', bucket, object_key)
    current_time = now()

    for sector in sectors:
        sector.refresh_from_db()

    assert f'Not disabling sector {sectors[2]} as it has children' in caplog.text
    assert len(caplog.records) == 1

    assert [sector.was_disabled_on(current_time) for sector in sectors] == [
        True, True, False,
    ]


def test_simulate(s3_stubber):
    """Test that the command simulates updates if --simulate is passed in."""
    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector_1', 'sector_2', 'sector_3']),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id
{sectors[0].pk}
{sectors[1].pk}
{sectors[2].pk}
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

    call_command('disable_sector', bucket, object_key, simulate=True)
    current_time = now()

    for sector in sectors:
        sector.refresh_from_db()

    assert not any([sector.was_disabled_on(current_time) for sector in sectors])


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    sector_with_change = SectorFactory(
        segment='sector_1',
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id
{sector_with_change.pk}
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

    call_command('disable_sector', bucket, object_key)

    versions = Version.objects.get_for_object(sector_with_change)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'Sector disable.'
