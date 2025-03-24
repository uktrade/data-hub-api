import pytest
from mptt.exceptions import InvalidMove

from datahub.core.constants import Sector as SectorConstants
from datahub.core.exceptions import DataHubError
from datahub.metadata.models import Sector, Service
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
    """Test that it's not possible to save a sector when it's part of a recursive hierarchy.
    """
    parent = SectorFactory()
    sector = SectorFactory(parent=parent)
    parent.parent = sector
    with pytest.raises(InvalidMove):
        parent.save()


def test_sector_name_recursive_via_parent_unsaved():
    """Test that accessing the path of a sector raises an exception when it's part of a recursive
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
    """Test that accessing the path of a sector raises an exception when its parent points at
    itself.
    """
    sector = SectorFactory()
    sector.parent = sector
    with pytest.raises(DataHubError):
        sector.name


@pytest.mark.parametrize(
    ('segments', 'expected_name'),
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
    ('name', 'expected_segments'),
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
    """Test that services with children have no context.

    Services with children are being shown depending on if any of their children
    have desired context.
    """
    services = Service.objects.filter(children__isnull=False)
    assert all(service.contexts == [] for service in services)
