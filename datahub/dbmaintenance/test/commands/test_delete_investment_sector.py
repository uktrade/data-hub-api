from io import BytesIO

import factory
import pytest
from django.core.management import call_command
from reversion.models import Version

from datahub.investment.project.models import FDISICGrouping, InvestmentSector
from datahub.investment.project.test.factories import (
    FDISICGroupingFactory,
    InvestmentSectorFactory,
)
from datahub.metadata.models import Sector
from datahub.metadata.test.factories import SectorFactory

pytestmark = pytest.mark.django_db


def test_happy_path(s3_stubber):
    """Test that command deletes specified investment sectors."""
    sectors = SectorFactory.create_batch(
        2,
        segment=factory.Iterator(['sector1', 'sector2']),
    )
    fdi_sic_groupings = FDISICGroupingFactory.create_batch(
        2,
        name=factory.Iterator(['fdi_sic_grouping1', 'fdi_sic_grouping2']),
    )
    investment_sectors = InvestmentSectorFactory.create_batch(
        2,
        sector=factory.Iterator([sectors[0], sectors[1]]),
        fdi_sic_grouping=factory.Iterator(
            [fdi_sic_groupings[0], fdi_sic_groupings[1]],
        ),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    headers = [
        'sector_id',
        'fdi_sic_grouping_id',
    ]
    data = [(sectors[0].pk, fdi_sic_groupings[0].pk)]

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

    call_command('delete_investment_sector', bucket, object_key)

    investment_sectors = InvestmentSector.objects.all()

    assert len(investment_sectors) == n_investment_sectors_before - 1
    investment_sectors = InvestmentSector.objects.filter(
        sector_id=sectors[1].pk,
    )
    assert len(investment_sectors) == 1
    assert investment_sectors[0].fdi_sic_grouping == fdi_sic_groupings[1]


def test_non_existent_investment_sector(s3_stubber, caplog):
    """Test that the command logs an error when the sector PK does not exist."""
    caplog.set_level('ERROR')

    bucket = 'test_bucket'
    object_key = 'test_key'
    headers = [
        'sector_id',
        'fdi_sic_grouping_id',
    ]
    data = [
        (
            Sector(segment='does not exist').id,
            FDISICGrouping(name='does not exist').id,
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

    call_command('delete_investment_sector', bucket, object_key)

    investment_sectors = InvestmentSector.objects.all()

    assert len(investment_sectors) == n_investment_sectors_before

    assert len(caplog.records) == 1
    assert 'InvestmentSector does not exist' in caplog.text


def test_simulate(s3_stubber):
    """Test that the command simulates updates if --simulate is passed in."""
    sectors = SectorFactory.create_batch(
        2,
        segment=factory.Iterator(['sector1', 'sector2']),
    )
    fdi_sic_groupings = FDISICGroupingFactory.create_batch(
        2,
        name=factory.Iterator(['fdi_sic_grouping1', 'fdi_sic_grouping2']),
    )
    investment_sectors = InvestmentSectorFactory.create_batch(
        2,
        sector=factory.Iterator([sectors[0], sectors[1]]),
        fdi_sic_grouping=factory.Iterator(
            [fdi_sic_groupings[0], fdi_sic_groupings[1]],
        ),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    headers = [
        'sector_id',
        'fdi_sic_grouping_id',
    ]

    data = [
        (sectors[0].pk, fdi_sic_groupings[0].pk),
        (sectors[1].pk, fdi_sic_groupings[1].pk),
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

    call_command('delete_investment_sector', bucket, object_key, simulate=True)

    investment_sectors = InvestmentSector.objects.all()

    assert len(investment_sectors) == n_investment_sectors_before
    assert len(InvestmentSector.objects.filter(sector=sectors[0])) == 1
    assert len(InvestmentSector.objects.filter(sector=sectors[1])) == 1


def test_audit_log(s3_stubber):
    """Test that reversion revisions are created."""
    sectors = SectorFactory.create_batch(
        2,
        segment=factory.Iterator(['sector1', 'sector2']),
    )
    fdi_sic_groupings = FDISICGroupingFactory.create_batch(
        2,
        name=factory.Iterator(['fdi_sic_grouping1', 'fdi_sic_grouping2']),
    )

    bucket = 'test_bucket'
    object_key = 'test_key'
    headers = [
        'sector_id',
        'fdi_sic_grouping_id',
    ]

    data = [
        (sectors[0].pk, fdi_sic_groupings[0].pk),
        (sectors[1].pk, fdi_sic_groupings[1].pk),
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

    call_command('delete_investment_sector', bucket, object_key)

    new_investment_sectors = InvestmentSector.objects.filter(
        sector_id__in=[d[0] for d in data],
    )

    for investment_sector in new_investment_sectors:
        versions = Version.objects.get_for_object(investment_sector)
        assert versions.count() == 1
        assert versions[0].revision.get_comment() == 'InvestmentSector deletion.'
