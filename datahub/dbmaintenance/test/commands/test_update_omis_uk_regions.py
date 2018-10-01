from io import BytesIO

import pytest
from django.core.management import call_command

from datahub.core import constants
from datahub.omis.order.test.factories import OrderFactory


pytestmark = pytest.mark.django_db


def test_run(s3_stubber):
    """Test that the command updates the relevant records ignoring ones with errors."""
    orders = [
        # order in CSV doesn't exist so row should fail

        # region should get updated
        OrderFactory(uk_region_id=None),
        # region should get updated
        OrderFactory(uk_region_id=constants.UKRegion.channel_islands.value.id),
        # region should become None
        OrderFactory(uk_region_id=constants.UKRegion.east_of_england.value.id),
        # should be ignored
        OrderFactory(uk_region_id=constants.UKRegion.fdi_hub.value.id),
        # region in the file doesn't exist so row should fail
        OrderFactory(uk_region_id=constants.UKRegion.isle_of_man.value.id),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""order_id,uk_region_id
00000000-0000-0000-0000-000000000000,{constants.UKRegion.guernsey.value.id}
{orders[0].id},{constants.UKRegion.england.value.id}
{orders[1].id},{constants.UKRegion.east_midlands.value.id}
{orders[2].id},NULL
{orders[4].id},00000000-0000-0000-0000-000000000000
"""

    s3_stubber.add_response(
        'get_object',
        {'Body': BytesIO(bytes(csv_content, encoding='utf-8'))},
        expected_params={'Bucket': bucket, 'Key': object_key},
    )

    call_command('update_omis_uk_regions', bucket, object_key)

    for order in orders:
        order.refresh_from_db()

    assert str(orders[0].uk_region.id) == constants.UKRegion.england.value.id
    assert str(orders[1].uk_region.id) == constants.UKRegion.east_midlands.value.id
    assert orders[2].uk_region is None
    assert str(orders[3].uk_region.id) == constants.UKRegion.fdi_hub.value.id
    assert str(orders[4].uk_region.id) == constants.UKRegion.isle_of_man.value.id


def test_simulate(s3_stubber):
    """Test that the command only simulates the actions if --simulate is passed in."""
    orders = [
        OrderFactory(uk_region_id=None),
        OrderFactory(uk_region_id=constants.UKRegion.channel_islands.value.id),
    ]

    bucket = 'test_bucket'
    object_key = 'test_key'
    csv_content = f"""order_id,uk_region_id
{orders[0].id},{constants.UKRegion.england.value.id}
{orders[1].id},{constants.UKRegion.east_midlands.value.id}
"""
    s3_stubber.add_response(
        'get_object',
        {'Body': BytesIO(bytes(csv_content, encoding='utf-8'))},
        expected_params={'Bucket': bucket, 'Key': object_key},
    )

    call_command('update_omis_uk_regions', bucket, object_key, simulate=True)

    for order in orders:
        order.refresh_from_db()

    assert orders[0].uk_region is None
    assert str(orders[1].uk_region.id) == constants.UKRegion.channel_islands.value.id
