import uuid

import pytest

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import (
    ExportFactory,
)
from datahub.core.test_utils import APITestMixin

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestDeleteExport(APITestMixin):
    """Test delete export"""

    def test_delete_unknown_export_returns_error(self):

        ExportFactory.create_batch(3)
        url = reverse('api-v4:export:item', kwargs={'pk': uuid.uuid4()})

        response = self.api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_success(self):

        export = ExportFactory()
        url = reverse('api-v4:export:item', kwargs={'pk': export.id})

        response = self.api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = self.api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
