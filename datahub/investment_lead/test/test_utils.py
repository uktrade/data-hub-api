import pytest

from datahub.investment_lead.test.factories import EYBLeadFactory
from datahub.investment_lead.test.utils import verify_eyb_lead_data


@pytest.mark.django_db
def test_verify_eyb_lead_data_raises_error_when_invalid_argument_is_passed(
    eyb_lead_factory_data,
):
    instance = EYBLeadFactory(**eyb_lead_factory_data)
    with pytest.raises(ValueError):
        verify_eyb_lead_data(instance, eyb_lead_factory_data, 'invalid_data_type')
