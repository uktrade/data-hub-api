import pytest
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.test import Client
from django.urls import reverse
from rest_framework import status

from datahub.company.models import Company, CompanyPermission
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import AdminTestMixin, create_test_user


@pytest.mark.usefixtures('merge_list_feature_flag')
class TestCompanyAdminPermissions(AdminTestMixin):
    """Test permission handling in various views."""

    @pytest.mark.parametrize(
        'route_name,needs_arg,method',
        (
            (
                admin_urlname(Company._meta, 'merge-select-other-company'),
                True,
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-select-primary-company'),
                False,
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-select-primary-company'),
                False,
                'post',
            ),
            (
                admin_urlname(Company._meta, 'merge-confirm'),
                False,
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-confirm'),
                False,
                'post',
            ),
        ),
    )
    def test_redirects_to_login_page_if_not_logged_in(self, route_name, needs_arg, method):
        """Test that the view redirects to the login page if the user isn't authenticated."""
        args = (CompanyFactory().pk,) if needs_arg else ()
        url = reverse(route_name, args=args)

        client = Client()
        request_func = getattr(client, method)
        response = request_func(url, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1
        assert response.redirect_chain[0][0] == self.login_url_with_redirect(url)

    @pytest.mark.parametrize(
        'route_name,needs_arg,method',
        (
            (
                admin_urlname(Company._meta, 'merge-select-other-company'),
                True,
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-select-primary-company'),
                False,
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-select-primary-company'),
                False,
                'post',
            ),
            (
                admin_urlname(Company._meta, 'merge-confirm'),
                False,
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-confirm'),
                False,
                'post',
            ),
        ),
    )
    def test_redirects_to_login_page_if_not_staff(self, route_name, needs_arg, method):
        """Test that the view redirects to the login page if the user isn't a member of staff."""
        args = (CompanyFactory().pk,) if needs_arg else ()
        url = reverse(route_name, args=args)

        user = create_test_user(is_staff=False, password=self.PASSWORD)
        client = self.create_client(user=user)
        request_func = getattr(client, method)

        response = request_func(url, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1
        assert response.redirect_chain[0][0] == self.login_url_with_redirect(url)

    @pytest.mark.parametrize(
        'route_name,needs_arg,method',
        (
            (
                admin_urlname(Company._meta, 'merge-select-other-company'),
                True,
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-select-primary-company'),
                False,
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-select-primary-company'),
                False,
                'post',
            ),
            (
                admin_urlname(Company._meta, 'merge-confirm'),
                False,
                'get',
            ),
            (
                admin_urlname(Company._meta, 'merge-confirm'),
                False,
                'post',
            ),
        ),
    )
    def test_permission_denied_if_staff_and_without_change_permission(
            self,
            route_name,
            needs_arg,
            method,
    ):
        """
        Test that the view returns a 403 response if the staff user does not have the
        change company permission.
        """
        args = (CompanyFactory().pk,) if needs_arg else ()
        url = reverse(route_name, args=args)

        user = create_test_user(
            permission_codenames=(CompanyPermission.view_company,),
            is_staff=True,
            password=self.PASSWORD,
        )
        client = self.create_client(user=user)
        request_func = getattr(client, method)

        response = request_func(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
