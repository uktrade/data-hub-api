from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.metadata.models import Sector
from datahub.metadata.test.factories import SectorClusterFactory, SectorFactory

pytestmark = pytest.mark.django_db


def test_happy_path(s3_stubber):
    """Test that the command creates the specified records."""
    sector_pks = [
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000003',
    ]
    segments = ['segment_1', 'segment_2', 'segment_3']
    clusters = SectorClusterFactory.create_batch(
        3,
        name=factory.Iterator(['cluster_1', 'cluster_2', 'cluster_3']),
    )
    parent_sector = SectorFactory()

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,segment,sector_cluster_id,parent_id
{sector_pks[0]},{segments[0]},{clusters[0].pk},{parent_sector.pk}
{sector_pks[1]},{segments[1]},{clusters[1].pk},{parent_sector.pk}
{sector_pks[2]},{segments[2]},{clusters[2].pk},{parent_sector.pk}
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

    call_command('create_sector', bucket, object_key)

    sectors = Sector.objects.filter(pk__in=sector_pks)
    assert len(sectors) == 3
    assert [str(sectors[0].pk), str(sectors[1].pk), str(sectors[2].pk)] == sector_pks
    assert [sectors[0].segment, sectors[1].segment, sectors[2].segment] == segments
    assert [
        sectors[0].sector_cluster,
        sectors[1].sector_cluster,
        sectors[2].sector_cluster,
    ] == clusters
    assert [
        sectors[0].parent,
        sectors[1].parent,
        sectors[2].parent,
    ] == [parent_sector, parent_sector, parent_sector]


def test_duplicate_sector(s3_stubber, caplog):
    """Test that the command logs an error when the sector PK already exists."""
    caplog.set_level('ERROR')

    sector_pks = [
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000003',
    ]
    segments = ['segment_1', 'segment_2', 'segment_3']
    clusters = SectorClusterFactory.create_batch(
        3,
        name=factory.Iterator(['cluster_1', 'cluster_2', 'cluster_3']),
    )
    parent_sector = SectorFactory()
    duplicate_sector = SectorFactory(id=sector_pks[2])

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,segment,sector_cluster_id,parent_id
{sector_pks[0]},{segments[0]},{clusters[0].pk},{parent_sector.pk}
{sector_pks[1]},{segments[1]},{clusters[1].pk},{parent_sector.pk}
{duplicate_sector.pk},{segments[2]},{clusters[2].pk},{parent_sector.pk}
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

    call_command('create_sector', bucket, object_key)

    sectors = Sector.objects.filter(pk__in=sector_pks)
    assert len(sectors) == 3

    assert f'Key (id)=({duplicate_sector.pk}) already exists' in caplog.text
    assert len(caplog.records) == 1

    assert [str(sectors[0].pk), str(sectors[1].pk), str(sectors[2].pk)] == sector_pks
    assert [sectors[0].segment, sectors[1].segment] == segments[:2]
    assert [sectors[0].sector_cluster, sectors[1].sector_cluster] == clusters[:2]
    assert [
        sectors[0].parent,
        sectors[1].parent,
    ] == [parent_sector, parent_sector]


def test_blank_parent(s3_stubber):
    """Test that the command creates the specified records when no parent is provided."""
    sector_pks = [
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000003',
    ]
    segments = ['segment_1', 'segment_2', 'segment_3']
    clusters = SectorClusterFactory.create_batch(
        3,
        name=factory.Iterator(['cluster_1', 'cluster_2', 'cluster_3']),
    )
    parent_sector = SectorFactory()

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,segment,sector_cluster_id,parent_id
{sector_pks[0]},{segments[0]},{clusters[0].pk},{parent_sector.pk}
{sector_pks[1]},{segments[1]},{clusters[1].pk},{parent_sector.pk}
{sector_pks[2]},{segments[2]},{clusters[2].pk},
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

    call_command('create_sector', bucket, object_key)

    sectors = Sector.objects.filter(pk__in=sector_pks)
    assert len(sectors) == 3
    assert [str(sectors[0].pk), str(sectors[1].pk), str(sectors[2].pk)] == sector_pks
    assert [sectors[0].segment, sectors[1].segment, sectors[2].segment] == segments
    assert [
        sectors[0].sector_cluster,
        sectors[1].sector_cluster,
        sectors[2].sector_cluster,
    ] == clusters
    assert [
        sectors[0].parent,
        sectors[1].parent,
        sectors[2].parent,
    ] == [parent_sector, parent_sector, None]


def test_blank_sector_cluster(s3_stubber):
    """Test that the command creates the specified records when no sector cluster is provided."""
    sector_pks = [
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000003',
    ]
    segments = ['segment_1', 'segment_2', 'segment_3']
    clusters = SectorClusterFactory.create_batch(
        3,
        name=factory.Iterator(['cluster_1', 'cluster_2', 'cluster_3']),
    )
    parent_sector = SectorFactory()

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,segment,sector_cluster_id,parent_id
{sector_pks[0]},{segments[0]},{clusters[0].pk},{parent_sector.pk}
{sector_pks[1]},{segments[1]},{clusters[1].pk},{parent_sector.pk}
{sector_pks[2]},{segments[2]},,{parent_sector.pk}
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

    call_command('create_sector', bucket, object_key)

    sectors = Sector.objects.filter(pk__in=sector_pks)
    assert len(sectors) == 3
    assert [str(sectors[0].pk), str(sectors[1].pk), str(sectors[2].pk)] == sector_pks
    assert [sectors[0].segment, sectors[1].segment, sectors[2].segment] == segments
    assert [sectors[0].sector_cluster, sectors[1].sector_cluster] == clusters[:2]
    assert not sectors[2].sector_cluster
    assert [
        sectors[0].parent,
        sectors[1].parent,
        sectors[2].parent,
    ] == [parent_sector, parent_sector, parent_sector]


def test_non_existent_parent(s3_stubber, caplog):
    """Test that the command logs an error when parent PK does not exist."""
    caplog.set_level('ERROR')

    sector_pks = [
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000003',
    ]
    segments = ['segment_1', 'segment_2', 'segment_3']
    clusters = SectorClusterFactory.create_batch(
        3,
        name=factory.Iterator(['cluster_1', 'cluster_2', 'cluster_3']),
    )
    parent_sector = SectorFactory()

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,segment,sector_cluster_id,parent_id
{sector_pks[0]},{segments[0]},{clusters[0].pk},{parent_sector.pk}
{sector_pks[1]},{segments[1]},{clusters[1].pk},{parent_sector.pk}
{sector_pks[2]},{segments[2]},{clusters[2].pk},00000000-0000-0000-0000-000000000000
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

    call_command('create_sector', bucket, object_key)

    sectors = Sector.objects.filter(pk__in=sector_pks)
    assert len(sectors) == 2

    assert 'Sector matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [str(sectors[0].pk), str(sectors[1].pk)] == sector_pks[:2]
    assert [sectors[0].segment, sectors[1].segment] == segments[:2]
    assert [sectors[0].sector_cluster, sectors[1].sector_cluster] == clusters[:2]
    assert [
        sectors[0].parent,
        sectors[1].parent,
    ] == [parent_sector, parent_sector]


def test_non_existent_sector_cluster(s3_stubber, caplog):
    """Test that the command logs an error when sector cluster PK does not exist."""
    caplog.set_level('ERROR')

    sector_pks = [
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000003',
    ]
    segments = ['segment_1', 'segment_2', 'segment_3']
    clusters = SectorClusterFactory.create_batch(
        3,
        name=factory.Iterator(['cluster_1', 'cluster_2', 'cluster_3']),
    )
    parent_sector = SectorFactory()

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,segment,sector_cluster_id,parent_id
{sector_pks[0]},{segments[0]},{clusters[0].pk},{parent_sector.pk}
{sector_pks[1]},{segments[1]},{clusters[1].pk},{parent_sector.pk}
{sector_pks[2]},{segments[2]},00000000-0000-0000-0000-000000000000,{parent_sector.pk}
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

    call_command('create_sector', bucket, object_key)

    sectors = Sector.objects.filter(pk__in=sector_pks)
    assert len(sectors) == 2

    assert 'SectorCluster matching query does not exist' in caplog.text
    assert len(caplog.records) == 1

    assert [str(sectors[0].pk), str(sectors[1].pk)] == sector_pks[:2]
    assert [sectors[0].segment, sectors[1].segment] == segments[:2]
    assert [sectors[0].sector_cluster, sectors[1].sector_cluster] == clusters[:2]
    assert [
        sectors[0].parent,
        sectors[1].parent,
    ] == [parent_sector, parent_sector]


def test_simulate(s3_stubber):
    """Test that the command simulates creations if --simulate is passed in."""
    sector_pks = [
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000003',
    ]
    segments = ['segment_1', 'segment_2', 'segment_3']
    clusters = SectorClusterFactory.create_batch(
        3,
        name=factory.Iterator(['cluster_1', 'cluster_2', 'cluster_3']),
    )
    parent_sector = SectorFactory()

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,segment,sector_cluster_id,parent_id
{sector_pks[0]},{segments[0]},{clusters[0].pk},{parent_sector.pk}
{sector_pks[1]},{segments[1]},{clusters[1].pk},{parent_sector.pk}
{sector_pks[2]},{segments[2]},{clusters[2].pk},{parent_sector.pk}
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

    call_command('create_sector', bucket, object_key, simulate=True)

    sectors = Sector.objects.filter(pk__in=sector_pks)
    assert not sectors


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    sector_pks = [
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000003',
    ]
    segments = ['segment_1', 'segment_2', 'segment_3']
    clusters = SectorClusterFactory.create_batch(
        3,
        name=factory.Iterator(['cluster_1', 'cluster_2', 'cluster_3']),
    )
    parent_sector = SectorFactory()

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""id,segment,sector_cluster_id,parent_id
{sector_pks[0]},{segments[0]},{clusters[0].pk},{parent_sector.pk}
{sector_pks[1]},{segments[1]},{clusters[1].pk},{parent_sector.pk}
{sector_pks[2]},{segments[2]},{clusters[2].pk},{parent_sector.pk}
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

    call_command('create_sector', bucket, object_key)

    sectors = Sector.objects.filter(pk__in=sector_pks)
    assert len(sectors) == 3

    for sector in sectors:
        versions = Version.objects.get_for_object(sector)
        assert versions.count() == 1
        assert versions[0].revision.get_comment() == 'Sector creation.'
