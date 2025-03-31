from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.investment.project.models import FDISICGrouping, InvestmentSector
from datahub.investment.project.test.factories import FDISICGroupingFactory
from datahub.metadata.models import Sector
from datahub.metadata.test.factories import SectorFactory

pytestmark = pytest.mark.django_db


def test_happy_path(s3_stubber):
    """Test that command creates specified investment sectors"""
    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector1', 'sector2', 'sector3']),
    )
    fdi_sic_groupings = FDISICGroupingFactory.create_batch(
        2,
        name=factory.Iterator(['fdi_sic_grouping1', 'fdi_sic_grouping2']),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    headers = [
        'sector_id',
        'sector',
        'fdi_sic_grouping_id',
        'fdi_sic_grouping_name',
    ]
    data = [
        (sectors[0].pk, 'path1', fdi_sic_groupings[0].pk, 'name1'),
        (sectors[1].pk, 'path2', fdi_sic_groupings[0].pk, 'name1'),
        (sectors[2].pk, 'path3', fdi_sic_groupings[1].pk, 'name2'),
    ]

    csv_content = ','.join(headers)
    for row in data:
        csv_content += '\n' + ','.join([str(col) for col in row])

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

    n_investment_sectors_before = len(InvestmentSector.objects.all())

    call_command('create_investment_sector', bucket, object_key)

    investment_sectors = InvestmentSector.objects.all()

    assert len(investment_sectors) == n_investment_sectors_before + 3

    for d in data:
        matches = InvestmentSector.objects.filter(sector_id=d[0])
        assert len(matches) == 1
        investment_sector = matches[0]
        assert investment_sector.fdi_sic_grouping_id == d[2]


def test_non_existent_sector(s3_stubber, caplog):
    """Test that the command logs an error when the sector PK does not exist."""
    caplog.set_level('ERROR')

    SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector1', 'sector2', 'sector3']),
    )
    fdi_sic_groupings = FDISICGroupingFactory.create_batch(
        2,
        name=factory.Iterator(['fdi_sic_grouping1', 'fdi_sic_grouping2']),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    headers = [
        'sector_id',
        'sector',
        'fdi_sic_grouping_id',
        'fdi_sic_grouping_name',
    ]
    data = [
        (
            Sector(segment='does not exist').id,
            'path1',
            fdi_sic_groupings[0].pk,
            'name1',
        ),
    ]

    csv_content = ','.join(headers)
    for row in data:
        csv_content += '\n' + ','.join([str(col) for col in row])

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

    n_investment_sectors_before = len(InvestmentSector.objects.all())

    call_command('create_investment_sector', bucket, object_key)

    investment_sectors = InvestmentSector.objects.all()

    assert len(investment_sectors) == n_investment_sectors_before

    assert len(caplog.records) == 1
    assert 'Sector matching query does not exist' in caplog.text


def test_non_existent_fdi_sic_grouping(s3_stubber, caplog):
    """Test that the command logs an error when the FDISICGrouping
    PK does not exist.
    """
    caplog.set_level('ERROR')

    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector1', 'sector2', 'sector3']),
    )
    FDISICGroupingFactory.create_batch(
        2,
        name=factory.Iterator(['fdi_sic_grouping1', 'fdi_sic_grouping2']),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    headers = [
        'sector_id',
        'sector',
        'fdi_sic_grouping_id',
        'fdi_sic_grouping_name',
    ]
    data = [
        (
            sectors[0].pk,
            'path1',
            FDISICGrouping(name='does not exist').pk,
            'name1',
        ),
    ]

    csv_content = ','.join(headers)
    for row in data:
        csv_content += '\n' + ','.join([str(col) for col in row])

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

    n_investment_sectors_before = len(InvestmentSector.objects.all())

    call_command('create_investment_sector', bucket, object_key)

    investment_sectors = InvestmentSector.objects.all()

    assert len(investment_sectors) == n_investment_sectors_before

    assert len(caplog.records) == 1
    assert 'FDISICGrouping matching query does not exist' in caplog.text


def test_entry_already_exists_for_sector(s3_stubber, caplog):
    """Test that the command ignores records for with sector_ids that already
    exist in the InvestmentSector table
    """
    caplog.set_level('ERROR')

    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector1', 'sector2', 'sector3']),
    )
    fdi_sic_groupings = FDISICGroupingFactory.create_batch(
        2,
        name=factory.Iterator(['fdi_sic_grouping1', 'fdi_sic_grouping2']),
    )
    investment_sector = InvestmentSector(
        sector=sectors[0],
        fdi_sic_grouping=fdi_sic_groupings[0],
    )
    investment_sector.save()

    bucket = 'test_bucket'
    object_key = 'test_key'
    headers = [
        'sector_id',
        'sector',
        'fdi_sic_grouping_id',
        'fdi_sic_grouping_name',
    ]
    data = [
        (sectors[0].pk, 'path1', fdi_sic_groupings[1].pk, 'name1'),
    ]

    csv_content = ','.join(headers)
    for row in data:
        csv_content += '\n' + ','.join([str(col) for col in row])

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

    n_investment_sectors_before = len(InvestmentSector.objects.all())

    call_command('create_investment_sector', bucket, object_key)

    investment_sectors = InvestmentSector.objects.all()

    assert len(investment_sectors) == n_investment_sectors_before

    assert len(caplog.records) == 1
    assert f'InvestmentSector for sector_id: {sectors[0].pk} already exists' in caplog.text


def test_simulate(s3_stubber):
    """Test that the command simulates updates if --simulate is passed in."""
    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector1', 'sector2', 'sector3']),
    )
    fdi_sic_groupings = FDISICGroupingFactory.create_batch(
        2,
        name=factory.Iterator(['fdi_sic_grouping1', 'fdi_sic_grouping2']),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    headers = [
        'sector_id',
        'sector',
        'fdi_sic_grouping_id',
        'fdi_sic_grouping_name',
    ]

    data = [
        (sectors[0].pk, 'path1', fdi_sic_groupings[0].pk, 'name1'),
        (sectors[1].pk, 'path2', fdi_sic_groupings[0].pk, 'name1'),
        (sectors[2].pk, 'path3', fdi_sic_groupings[1].pk, 'name2'),
    ]

    csv_content = ','.join(headers)
    for row in data:
        csv_content += '\n' + ','.join([str(col) for col in row])

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

    n_investment_sectors_before = len(InvestmentSector.objects.all())

    call_command('create_investment_sector', bucket, object_key, simulate=True)

    investment_sectors = InvestmentSector.objects.all()

    assert len(investment_sectors) == n_investment_sectors_before


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    sectors = SectorFactory.create_batch(
        3,
        segment=factory.Iterator(['sector1', 'sector2', 'sector3']),
    )
    fdi_sic_groupings = FDISICGroupingFactory.create_batch(
        2,
        name=factory.Iterator(['fdi_sic_grouping1', 'fdi_sic_grouping2']),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    headers = [
        'sector_id',
        'sector',
        'fdi_sic_grouping_id',
        'fdi_sic_grouping_name',
    ]

    data = [
        (sectors[0].pk, 'path1', fdi_sic_groupings[0].pk, 'name1'),
        (sectors[1].pk, 'path2', fdi_sic_groupings[0].pk, 'name1'),
        (sectors[2].pk, 'path3', fdi_sic_groupings[1].pk, 'name2'),
    ]

    csv_content = ','.join(headers)
    for row in data:
        csv_content += '\n' + ','.join([str(col) for col in row])

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

    call_command('create_investment_sector', bucket, object_key)

    new_investment_sectors = InvestmentSector.objects.filter(
        sector_id__in=[d[0] for d in data],
    )

    for investment_sector in new_investment_sectors:
        versions = Version.objects.get_for_object(investment_sector)
        assert versions.count() == 1
        assert versions[0].revision.get_comment() == 'InvestmentSector creation.'
