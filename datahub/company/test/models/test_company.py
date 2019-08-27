import pytest

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory


@pytest.mark.django_db
def test_failed_dnb_investigation():
    """
    Check if a newly create company has `failed_dnb_investigation`
    set to False.
    """
    company = CompanyFactory()
    assert not Company.objects.get(
        id=company.id,
    ).failed_dnb_investigation
