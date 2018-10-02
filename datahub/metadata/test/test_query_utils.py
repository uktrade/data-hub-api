import pytest

from datahub.metadata.models import Sector
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.metadata.test.factories import SectorFactory

pytestmark = pytest.mark.django_db


def test_annotated_sector_name_root_node():
    """Test the sector name annotation for a sector at root level."""
    sector = SectorFactory(parent=None)
    annotated_sector = Sector.objects.annotate(
        name_annotation=get_sector_name_subquery(),
    ).get(
        pk=sector.pk,
    )

    assert annotated_sector.name_annotation == sector.name


def test_annotated_sector_name_level_one():
    """Test the sector name annotation for a sector one level deep."""
    parent = SectorFactory()
    sector = SectorFactory(parent=parent)
    annotated_sector = Sector.objects.annotate(
        name_annotation=get_sector_name_subquery(),
    ).get(
        pk=sector.pk,
    )

    assert annotated_sector.name_annotation == sector.name


def test_annotated_sector_name_level_two():
    """Test the sector name annotation for a sector two levels deep."""
    grandparent = SectorFactory()
    parent = SectorFactory(parent=grandparent)
    sector = SectorFactory(parent=parent)
    annotated_sector = Sector.objects.annotate(
        name_annotation=get_sector_name_subquery(),
    ).get(
        pk=sector.pk,
    )

    assert annotated_sector.name_annotation == sector.name


def test_annotated_sector_name_via_relation():
    """Test the sector name annotation via a relation."""
    grandparent = SectorFactory()
    parent = SectorFactory(parent=grandparent)
    sector = SectorFactory(parent=parent)
    annotated_sector = Sector.objects.annotate(
        parent_name_annotation=get_sector_name_subquery('parent'),
    ).get(
        pk=sector.pk,
    )

    assert annotated_sector.parent_name_annotation == parent.name
