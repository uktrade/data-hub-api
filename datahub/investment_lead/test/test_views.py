import pytest

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from rest_framework import status
from rest_framework.reverse import reverse


from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.test.utils import (
    verify_eyb_lead_data
)


class TestDNBCompanyCreateAPI(APITestMixin):
    """
    EYB Lead Create view test case.
    """

    def test_post_with_no_payload(self):
        """
        Test that we get an Exception when no payload is sent
        """
        with pytest.raises(ImproperlyConfigured):
            self.api_client.post(
                reverse('api-v4:investment-lead:eyb-lead-create'),
                data=None,
            )
