from uuid import UUID

import pytest

from datahub.company.constants import BusinessTypeConstant
from datahub.metadata.models import BusinessType

pytestmark = pytest.mark.django_db


def test_company_business_type_post_migrate():
    """Test that business types have been correctly loaded."""
    loaded_business_types = {(obj.id, obj.name) for obj in BusinessType.objects.all()}
    expected_business_types = {(UUID(obj.value.id), obj.value.name)
                               for obj in BusinessTypeConstant}
    assert loaded_business_types == expected_business_types
