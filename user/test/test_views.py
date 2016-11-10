from django.urls import reverse
from rest_framework import status

from core.test_utils import LeelooTestCase, get_test_user


class UserViewTestCase(LeelooTestCase):

    def test_who_am_i_authenticated(self):

        url = reverse('who_am_i')
        response = self.api_client.get(url)
        user_test = get_test_user()

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == user_test.advisor.name
        assert response.data['first_name'] == user_test.advisor.first_name
        assert response.data['last_name'] == user_test.advisor.last_name
        assert response.data['id'] == str(user_test.advisor.pk)
