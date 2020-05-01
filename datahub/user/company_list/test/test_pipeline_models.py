import pytest

from datahub.user.company_list.test.factories import PipelineItemFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestPipelineItem:
    """Tests Pipeline item model"""

    def test_str(self):
        """Test the human friendly string representation of the object."""
        pipeline_item = PipelineItemFactory()
        status = f'{pipeline_item.company} - {pipeline_item.name} - {pipeline_item.status}'
        assert str(pipeline_item) == status
