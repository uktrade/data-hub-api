import pytest
from django.db.utils import IntegrityError

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.user.company_list.test.factories import PipelineItemFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestPipelineItem:
    """Tests Pipeline item model"""

    def test_str(self):
        """Test the human friendly string representation of the object."""
        pipeline_item = PipelineItemFactory()
        status = f'{pipeline_item.company} - {pipeline_item.adviser} - {pipeline_item.status}'
        assert str(pipeline_item) == status

    def test_unique_constraint(self):
        """
        Test unique constraint.
        A company and adviser combination can't be added more than once.
        """
        company = CompanyFactory()
        adviser = AdviserFactory()

        PipelineItemFactory(
            company=company,
            adviser=adviser,
        )

        with pytest.raises(IntegrityError):
            PipelineItemFactory(
                company=company,
                adviser=adviser,
            )
