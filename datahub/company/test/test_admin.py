import pytest
from django.contrib.admin import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.test.client import Client
from django.urls import reverse
from rest_framework import status

from datahub.company.test.factories import AdviserFactory

pytestmark = pytest.mark.django_db


def test_enable_users_action():
    """Enable users admin action."""
    user_model = get_user_model()
    password = 'password'
    admin_user = user_model.objects.create_superuser(email='admin@foo.bar', password=password)
    client = Client()
    client.login(username=admin_user.email, password=password)
    url = reverse('admin:company_advisor_changelist')
    user1 = AdviserFactory(use_cdms_auth=False)
    user2 = AdviserFactory(use_cdms_auth=False)
    data = {
        'action': 'enable_users',
        ACTION_CHECKBOX_NAME: [user1.pk, user2.pk]
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == status.HTTP_200_OK
    user1.refresh_from_db()
    user2.refresh_from_db()
    assert user1.use_cdms_auth
    assert user2.use_cdms_auth


def test_disable_users_action():
    """Disable users admin action."""
    user_model = get_user_model()
    password = 'password'
    admin_user = user_model.objects.create_superuser(email='admin@foo.bar', password=password)
    client = Client()
    client.login(username=admin_user.email, password=password)
    url = reverse('admin:company_advisor_changelist')
    user1 = AdviserFactory(use_cdms_auth=True)
    user2 = AdviserFactory(use_cdms_auth=True)
    data = {
        'action': 'disable_users',
        ACTION_CHECKBOX_NAME: [user1.pk, user2.pk]
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == status.HTTP_200_OK
    user1.refresh_from_db()
    user2.refresh_from_db()
    assert user1.use_cdms_auth is False
    assert user2.use_cdms_auth is False
