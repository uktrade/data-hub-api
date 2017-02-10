from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import get_test_user, LeelooTestCase


class UserViewTestCase(LeelooTestCase):
    """User view test case."""

    def test_who_am_i_authenticated(self):
        """Who am I."""
        url = reverse('who_am_i')
        response = self.api_client.get(url)
        user_test = get_test_user()

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == user_test.name
        assert response.data['first_name'] == user_test.first_name
        assert response.data['id'] == str(user_test.pk)
