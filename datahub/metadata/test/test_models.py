import pytest
from mptt.exceptions import InvalidMove

from datahub.core.exceptions import DataHubException
from datahub.metadata.models import Service
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
    with pytest.raises(DataHubException):
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
    with pytest.raises(DataHubException):
        sector.name


def test_service_with_children_has_no_contexts():
    """
    Test that services with children have no context.

    Services with children are being shown depending on if any of their children
    have desired context.
    """
    services = Service.objects.filter(children__isnull=False)
    assert all(service.contexts == [] for service in services)
