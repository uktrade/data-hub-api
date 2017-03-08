import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.core import constants

# mark the whole module for db use
pytestmark = pytest.mark.django_db


def test_company_model_sets_classification_to_undefined():
    """Test setting classification to undef by default."""
    c = CompanyFactory()  # Calls save
    assert c.classification_id == constants.CompanyClassification.undefined.value.id
