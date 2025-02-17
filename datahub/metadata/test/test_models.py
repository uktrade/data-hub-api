import logging

from unittest import mock

import pytest
from moto import mock_aws
from mptt.exceptions import InvalidMove

from datahub.core.constants import Sector as SectorConstants
from datahub.core.exceptions import DataHubError
from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.metadata.models import Sector, Service
from datahub.metadata.tasks import (
    postcode_data_identification_task,
    postcode_data_ingestion_task,
    POSTCODE_DATA_PREFIX,
)
from datahub.metadata.test.factories import SectorFactory

pytestmark = pytest.mark.django_db


def test_sector_name_root_node():
    """Test the sector path for a sector at root level."""
    sector = SectorFactory(parent=None)

    assert sector.name == sector.segment


def test_sector_name_level_one():
    """Test the sector path for a sector one level deep."""
    parent = SectorFactory()
    sector = SectorFactory(parent=parent)

    assert sector.name == f'{parent.segment} : {sector.segment}'


def test_sector_name_level_two():
    """Test the sector path for a sector two levels deep."""
    grandparent = SectorFactory()
    parent = SectorFactory(parent=grandparent)
    sector = SectorFactory(parent=parent)

    assert sector.name == f'{grandparent.segment} : {parent.segment} : {sector.segment}'


def test_sector_save_recursive_via_parent():
    """
    Test that it's not possible to save a sector when it's part of a recursive hierarchy.
    """
    parent = SectorFactory()
    sector = SectorFactory(parent=parent)
    parent.parent = sector
    with pytest.raises(InvalidMove):
        parent.save()


def test_sector_name_recursive_via_parent_unsaved():
    """
    Test that accessing the path of a sector raises an exception when it's part of a recursive
    hierarchy.
    """
    parent = SectorFactory()
    sector = SectorFactory(parent=parent)
    parent.parent = sector
    with pytest.raises(DataHubError):
        sector.name


def test_sector_save_recursive():
    """Test that it's not possible to save a sector with its parent pointing at itself."""
    sector = SectorFactory()
    sector.parent = sector
    with pytest.raises(InvalidMove):
        sector.save()


def test_sector_name_level_recursive_unsaved():
    """
    Test that accessing the path of a sector raises an exception when its parent points at
    itself.
    """
    sector = SectorFactory()
    sector.parent = sector
    with pytest.raises(DataHubError):
        sector.name


@pytest.mark.parametrize(
    ['segments', 'expected_name'],
    [
        (
            ['Level 0', 'Level 1', 'Level 2'],
            'Level 0 : Level 1 : Level 2',
        ),
        (
            ['Level 0', 'Level 1', None],
            'Level 0 : Level 1',
        ),
        (
            ['Level 0', None, None],
            'Level 0',
        ),
        (
            ['Level 0', '', ''],
            'Level 0',
        ),
        (
            [None, None, None],
            '',
        ),
    ],
)
def test_get_name_from_segments(segments, expected_name):
    """Tests the correct name is returned from a list of segments."""
    assert Sector.get_name_from_segments(segments) == expected_name


@pytest.mark.parametrize(
    ['name', 'expected_segments'],
    [
        (
            'Level 0 : Level 1 : Level 2',
            ('Level 2', 'Level 1'),
        ),
        (
            'Level 0 : Level 1',
            ('Level 1', 'Level 0'),
        ),
        (
            'Level 0',
            ('Level 0', None),
        ),
        (
            None,
            None,
        ),
    ],
)
def test_get_selected_and_parent_segments(name, expected_segments):
    """Tests the correct segments are selected from a name."""
    assert Sector.get_selected_and_parent_segments(name) == expected_segments


def test_get_segments_from_sector_instance():
    """Tests the correct segments are returned from a sector instance."""
    assert Sector.get_segments_from_sector_instance(
        Sector.objects.get(pk=SectorConstants.mining.value.id),
    ) == ('Mining', None, None)

    assert Sector.get_segments_from_sector_instance(
        Sector.objects.get(pk=SectorConstants.defence_land.value.id),
    ) == ('Defence', 'Land', None)

    assert Sector.get_segments_from_sector_instance(
        Sector.objects.get(pk=SectorConstants.renewable_energy_wind.value.id),
    ) == ('Energy', 'Renewable energy', 'Fixed-bottom offshore wind')


def test_service_with_children_has_no_contexts():
    """
    Test that services with children have no context.

    Services with children are being shown depending on if any of their children
    have desired context.
    """
    services = Service.objects.filter(children__isnull=False)
    assert all(service.contexts == [] for service in services)


class TestPostcodeDataIngestionTask:

    @pytest.fixture
    def postcode_object_key():
        return f'{POSTCODE_DATA_PREFIX}object.json.gz'

    @mock_aws
    def test_identification_task_schedules_ingestion_task(self, postcode_object_key, caplog):
        with (
            mock.patch('datahub.ingest.tasks.job_scheduler') as mock_scheduler,
            mock.patch.object(
                S3ObjectProcessor, 'get_most_recent_object_key', return_value=postcode_object_key,
            ),
            mock.patch.object(S3ObjectProcessor, 'has_object_been_ingested', return_value=False),
            caplog.at_level(logging.INFO),
        ):
            postcode_data_identification_task()

            assert 'Postcode data identification task started...' in caplog.text
            assert f'Scheduled ingestion of {postcode_object_key}' in caplog.text
            assert 'Postcode identification task finished.' in caplog.text

        mock_scheduler.assert_called_once_with(
            function=postcode_data_ingestion_task,
            function_kwargs={
                'object_key': postcode_object_key,
            },
            queue_name='long-running',
            description=f'Ingest {postcode_object_key}',
        )
