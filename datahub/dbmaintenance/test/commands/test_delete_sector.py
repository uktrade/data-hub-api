from io import BytesIO

import factory
import pytest
from django.core.management import call_command

from datahub.company.test.factories import CompanyFactory
from datahub.metadata.models import Sector
from datahub.metadata.test.factories import SectorFactory

pytestmark = pytest.mark.django_db


def test_happy_path(s3_stubber):
    """Test that the command deletes the specified records."""
    sector_pks = [
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000003',
    ]
    sectors = SectorFactory.create_batch(
        3,
        id=factory.Iterator(sector_pks),
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

    call_command('delete_sector', bucket, object_key)

    sectors = Sector.objects.filter(pk__in=sector_pks)
    assert not sectors


def test_non_existent_sector(s3_stubber, caplog):
    """Test that the command logs an error when PK does not exist."""
    caplog.set_level('ERROR')

    sector_pks = [
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000003',
    ]
    sectors = SectorFactory.create_batch(
        3,
        id=factory.Iterator(sector_pks),
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

    call_command('delete_sector', bucket, object_key)

    sectors = Sector.objects.filter(pk__in=sector_pks)

    assert 'Sector matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert len(sectors) == 1
    assert str(sectors[0].pk) == sector_pks[2]


def test_sector_with_children(s3_stubber, caplog):
    """Test that the command logs a warning if the sector has children."""
    caplog.set_level('WARNING')

    sector_pks = [
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000003',
    ]
    sectors = SectorFactory.create_batch(
        3,
        id=factory.Iterator(sector_pks),
    )

    # Create a child belonging to sector 3
    SectorFactory(parent=sectors[2])

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

    call_command('delete_sector', bucket, object_key)

    sectors = Sector.objects.filter(pk__in=sector_pks)

    assert f'Not deleting sector {sectors[0]} as it is referenced by another object' in caplog.text
    assert len(caplog.records) == 1

    assert len(sectors) == 1
    assert str(sectors[0].pk) == sector_pks[2]


def test_sector_with_referenced_objects(s3_stubber, caplog):
    """Test that the command logs a warning if the sector is referenced by another model."""
    caplog.set_level('WARNING')

    sector_pks = [
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000003',
    ]
    sectors = SectorFactory.create_batch(
        3,
        id=factory.Iterator(sector_pks),
    )

    # Create a company that is attached to sector 3
    CompanyFactory(sector_id=sectors[2].pk)

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

    call_command('delete_sector', bucket, object_key)

    sectors = Sector.objects.filter(pk__in=sector_pks)

    assert f'Not deleting sector {sectors[0]} as it is referenced by another object' in caplog.text
    assert len(caplog.records) == 1

    assert len(sectors) == 1
    assert str(sectors[0].pk) == sector_pks[2]


def test_simulate(s3_stubber):
    """Test that the command simulates deletes if --simulate is passed in."""
    sector_pks = [
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000003',
    ]
    sectors = SectorFactory.create_batch(
        3,
        id=factory.Iterator(sector_pks),
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

    call_command('delete_sector', bucket, object_key, simulate=True)

    sectors = Sector.objects.filter(pk__in=sector_pks)
    assert [str(sector.pk) for sector in sectors] == sector_pks
