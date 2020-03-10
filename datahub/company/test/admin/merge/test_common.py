import pytest
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.test import Client
from django.urls import reverse
from rest_framework import status

from datahub.company.models import Company, CompanyPermission
from datahub.core.test_utils import AdminTestMixin, create_test_user


class TestCompanyAdminPermissions(AdminTestMixin):
    """Test permission handling in various views."""

    @pytest.mark.parametrize(
        'route_name,method',
        (
            (
                admin_urlname(Company._meta, 'merge-select-other-company'),
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-select-primary-company'),
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-select-primary-company'),
                'post',
            ),
            (
                admin_urlname(Company._meta, 'merge-confirm'),
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-confirm'),
                'post',
            ),
        ),
    )
    def test_redirects_to_login_page_if_not_logged_in(self, route_name, method):
        """Test that the view redirects to the login page if the user isn't authenticated."""
        url = reverse(route_name)

        client = Client()
        request_func = getattr(client, method)
        response = request_func(url)

        assert response.status_code == status.HTTP_302_FOUND
        assert response['Location'] == self.login_url_with_redirect(url)

    @pytest.mark.parametrize(
        'route_name,method',
        (
            (
                admin_urlname(Company._meta, 'merge-select-other-company'),
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-select-primary-company'),
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-select-primary-company'),
                'post',
            ),
            (
                admin_urlname(Company._meta, 'merge-confirm'),
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-confirm'),
                'post',
            ),
        ),
    )
    def test_redirects_to_login_page_if_not_staff(self, route_name, method):
        """Test that the view redirects to the login page if the user isn't a member of staff."""
        url = reverse(route_name)

        user = create_test_user(is_staff=False, password=self.PASSWORD)
        client = self.create_client(user=user)
        request_func = getattr(client, method)

        response = request_func(url)

        assert response.status_code == status.HTTP_302_FOUND
        assert response['Location'] == self.login_url_with_redirect(url)

    @pytest.mark.parametrize(
        'route_name,method',
        (
            (
                admin_urlname(Company._meta, 'merge-select-other-company'),
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-select-primary-company'),
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-select-primary-company'),
                'post',
            ),
            (
                admin_urlname(Company._meta, 'merge-confirm'),
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-confirm'),
                'post',
            ),
        ),
    )
    def test_permission_denied_if_staff_and_without_change_permission(
            self,
            route_name,
            method,
    ):
        """
        Test that the view returns a 403 response if the staff user does not have the
        change company permission.
        """
        url = reverse(route_name)

        user = create_test_user(
            permission_codenames=(CompanyPermission.view_company,),
            is_staff=True,
            password=self.PASSWORD,
        )
        client = self.create_client(user=user)
        request_func = getattr(client, method)

        response = request_func(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
