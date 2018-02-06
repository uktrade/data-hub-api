from django.urls import reverse
from rest_framework import status

from datahub.core.test_utils import AdminTestMixin

from ..models import TermsAndConditions


class TestTermsAndConditionsAdmin(AdminTestMixin):
    """Tests for the TermsAndConditionsAdmin."""

    def test_can_add(self):
        """Test that terms and conditions records can be added."""
        url = reverse('admin:omis-quote_termsandconditions_add')
        data = {'name': 'v1', 'content': 'some content'}
        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert TermsAndConditions.objects.filter(name='v1').exists()

        terms = TermsAndConditions.objects.get(name='v1')
        assert terms.content == 'some content'

    def test_cannot_delete(self):
        """Test that terms and conditions records cannot be deleted."""
        terms = TermsAndConditions.objects.create(name='vtest', content='lorem ipsum')

        url = reverse('admin:omis-quote_termsandconditions_delete', args=(terms.id,))
        response = self.client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_change(self):
        """Test that terms and conditions records cannot be changed."""
        terms = TermsAndConditions.objects.create(name='vtest', content='lorem ipsum')

        url = reverse('admin:omis-quote_termsandconditions_change', args=(terms.id,))
        data = {'name': 'v2', 'content': 'new content'}
        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK
        terms.refresh_from_db()

        assert terms.name == 'vtest'
        assert terms.content == 'lorem ipsum'
