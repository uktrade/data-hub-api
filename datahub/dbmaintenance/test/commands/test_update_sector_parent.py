from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.metadata.test.factories import SectorFactory

pytestmark = pytest.mark.django_db


def test_happy_path(s3_stubber):
    """Test that the command updates the specified records."""
    sectors = ['sector_1', 'sector_2', 'section_3']
    old_parents = ['sector_1_parent_old', 'sector_2_parent_old', 'sector_3_parent_old']
    new_parents = ['sector_1_parent_new', 'sector_2_parent_new', 'sector_3_parent_new']

    old_parents = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(old_parents),
    )

    new_parents = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(new_parents),
    )

    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(sectors),
        parent=factory.Iterator(old_parents),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_parent_id,new_parent_id
{sectors[0].pk},{old_parents[0].pk},{new_parents[0].pk}
{sectors[1].pk},{old_parents[1].pk},{new_parents[1].pk}
{sectors[2].pk},{old_parents[2].pk},{new_parents[2].pk}
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

    call_command('update_sector_parent', bucket, object_key)

    for sector in sectors:
        sector.refresh_from_db()

    assert [sector.parent.pk for sector in sectors] == [parent.pk for parent in new_parents]


def test_non_existent_sector(s3_stubber, caplog):
    """Test that the command logs an error when the sector PK does not exist."""
    caplog.set_level('ERROR')

    sectors = ['sector_1', 'sector_2', 'section_3']
    old_parents = ['sector_1_parent_old', 'sector_2_parent_old', 'sector_3_parent_old']
    new_parents = ['sector_1_parent_new', 'sector_2_parent_new', 'sector_3_parent_new']

    old_parents = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(old_parents),
    )

    new_parents = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(new_parents),
    )

    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(sectors),
        parent=factory.Iterator(old_parents),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_parent_id,new_parent_id
{sectors[0].pk},{old_parents[0].pk},{new_parents[0].pk}
{sectors[1].pk},{old_parents[1].pk},{new_parents[1].pk}
00000000-0000-0000-0000-000000000000,{old_parents[2].pk},{new_parents[2].pk}
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

    call_command('update_sector_parent', bucket, object_key)

    for sector in sectors:
        sector.refresh_from_db()

    assert 'Sector matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [sector.parent.pk for sector in sectors] == [
        new_parents[0].pk, new_parents[1].pk, old_parents[2].pk,
    ]


def test_non_existent_sector_parent(s3_stubber, caplog):
    """Test that the command logs an error when the parent PK does not exist."""
    caplog.set_level('ERROR')

    sectors = ['sector_1', 'sector_2', 'section_3']
    old_parents = ['sector_1_parent_old', 'sector_2_parent_old', 'sector_3_parent_old']
    new_parents = ['sector_1_parent_new', 'sector_2_parent_new', 'sector_3_parent_new']

    old_parents = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(old_parents),
    )

    new_parents = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(new_parents),
    )

    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(sectors),
        parent=factory.Iterator(old_parents),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_parent_id,new_parent_id
{sectors[0].pk},{old_parents[0].pk},{new_parents[0].pk}
{sectors[1].pk},{old_parents[1].pk},{new_parents[1].pk}
{sectors[2].pk},{old_parents[2].pk},00000000-0000-0000-0000-000000000000
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

    call_command('update_sector_parent', bucket, object_key)

    for sector in sectors:
        sector.refresh_from_db()

    assert 'Sector matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [sector.parent.pk for sector in sectors] == [
        new_parents[0].pk, new_parents[1].pk, old_parents[2].pk,
    ]


def test_no_change(s3_stubber, caplog):
    """Test that the command ignores records that haven't changed
    or records with incorrect current values.
    """
    caplog.set_level('WARNING')

    sectors = ['sector_1', 'sector_2', 'section_3']
    old_parents = ['sector_1_parent_old', 'sector_2_parent_old', 'sector_3_parent_old']
    new_parents = ['sector_1_parent_new', 'sector_2_parent_new', 'sector_3_parent_new']

    old_parents = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(old_parents),
    )

    new_parents = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(new_parents),
    )

    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(sectors),
        parent=factory.Iterator(old_parents),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_parent_id,new_parent_id
{sectors[0].pk},{old_parents[0].pk},{new_parents[0].pk}
{sectors[1].pk},{old_parents[1].pk},{old_parents[1].pk}
{sectors[2].pk},00000000-0000-0000-0000-000000000000,{new_parents[1].pk}
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

    call_command('update_sector_parent', bucket, object_key)

    for sector in sectors:
        sector.refresh_from_db()

    assert f'Not updating sector {sectors[1]} as its parent has not changed' in caplog.text
    assert f'Not updating sector {sectors[2]} as its parent has not changed' in caplog.text
    assert len(caplog.records) == 2

    assert [sector.parent.pk for sector in sectors] == [
        new_parents[0].pk, old_parents[1].pk, old_parents[2].pk,
    ]


def test_simulate(s3_stubber):
    """Test that the command simulates updates if --simulate is passed in."""
    sectors = ['sector_1', 'sector_2', 'section_3']
    old_parents = ['sector_1_parent_old', 'sector_2_parent_old', 'sector_3_parent_old']
    new_parents = ['sector_1_parent_new', 'sector_2_parent_new', 'sector_3_parent_new']

    old_parents = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(old_parents),
    )

    new_parents = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(new_parents),
    )

    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(sectors),
        parent=factory.Iterator(old_parents),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_parent_id,new_parent_id
{sectors[0].pk},{old_parents[0].pk},{new_parents[0].pk}
{sectors[1].pk},{old_parents[1].pk},{new_parents[1].pk}
{sectors[2].pk},{old_parents[2].pk},{new_parents[2].pk}
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

    call_command('update_sector_parent', bucket, object_key, simulate=True)

    for sector in sectors:
        sector.refresh_from_db()

    assert [sector.parent.pk for sector in sectors] == [parent.pk for parent in old_parents]


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    new_parent = SectorFactory(
        segment='sector_1_parent_new',
    )

    sector_without_change = SectorFactory(
        segment='sector_1',
        parent=SectorFactory(
            segment='sector_1_parent_old',
        ),
    )

    sector_with_change = SectorFactory(
        segment='sector_2',
        parent=SectorFactory(
            segment='sector_2_parent_old',
        ),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,old_parent_id,new_parent_id
{sector_without_change.pk},{sector_without_change.parent.pk},{sector_without_change.parent.pk}
{sector_with_change.pk},{sector_with_change.parent.pk},{new_parent.pk}
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

    call_command('update_sector_parent', bucket, object_key)

    versions = Version.objects.get_for_object(sector_without_change)
    assert versions.count() == 0

    versions = Version.objects.get_for_object(sector_with_change)
    assert versions.count() == 1
    assert versions[0].revision.get_comment() == 'Sector parent correction.'
