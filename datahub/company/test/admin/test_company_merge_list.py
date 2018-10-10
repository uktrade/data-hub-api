from uuid import uuid4

import pytest
from django.contrib import messages as django_messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.test import Client
from django.urls import reverse
from rest_framework import status

from datahub.company.admin.company_merge_list import (
    MERGE_LIST_FEATURE_FLAG,
    MERGE_LIST_SESSION_KEY,
)
from datahub.company.models import Company, CompanyPermission
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import AdminTestMixin, create_test_user
from datahub.feature_flag.test.factories import FeatureFlagFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def merge_list_feature_flag():
    """Creates the merge list feature flag."""
    yield FeatureFlagFactory(code=MERGE_LIST_FEATURE_FLAG)


class TestAddToMergeList(AdminTestMixin):
    """Tests for the add to merge list button on the change form page."""

    def test_add_company_to_merge_list_button_is_shown(self):
        """Test that the button to add a company to the merge list is shown."""
        company = CompanyFactory()

        change_route_name = admin_urlname(Company._meta, 'change')
        change_url = reverse(change_route_name, args=(company.id,))

        response = self.client.get(change_url)

        add_to_list_route_name = admin_urlname(Company._meta, 'add-to-merge-list')
        add_to_list_url = reverse(add_to_list_route_name, args=(company.id,))

        assert add_to_list_url in response.rendered_content

    def test_can_add_company_to_merge_list(self):
        """Test that a company can be added to the merge list."""
        company = CompanyFactory()

        add_to_list_route_name = admin_urlname(Company._meta, 'add-to-merge-list')
        add_to_list_url = reverse(add_to_list_route_name, args=(company.id,))

        response = self.client.post(add_to_list_url, follow=True)
        session = self.client.session

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1

        changelist_route_name = admin_urlname(Company._meta, 'changelist')
        changelist_url = reverse(changelist_route_name)

        assert response.redirect_chain[0][0] == changelist_url
        assert session[MERGE_LIST_SESSION_KEY] == [str(company.pk)]

        merge_list_route_name = admin_urlname(Company._meta, 'merge-list')
        merge_list_url = reverse(merge_list_route_name)

        messages = list(response.context['messages'])
        assert len(messages) == 1
        assert messages[0].level == django_messages.SUCCESS
        assert messages[0].message == (
            f'1 item added to the merge list. <a href="{merge_list_url}">View merge list</a>.'
        )


class TestViewMergeList(AdminTestMixin):
    """Tests for the merge list page."""

    def test_added_companies_are_listed(self):
        """Test that companies in the merge list are listed."""
        companies = CompanyFactory.create_batch(3)
        session = self.client.session
        session[MERGE_LIST_SESSION_KEY] = [str(company.pk) for company in companies]
        session.save()

        merge_list_route_name = admin_urlname(Company._meta, 'merge-list')
        merge_list_url = reverse(merge_list_route_name)

        response = self.client.get(merge_list_url)

        assert response.status_code == status.HTTP_200_OK
        assert all(str(company.pk) in response.rendered_content for company in companies)

    def test_invalid_companies_are_ignored(self):
        """Test that companies in the merge list are listed."""
        company = CompanyFactory()
        non_existent_uuid = uuid4()

        session = self.client.session
        session[MERGE_LIST_SESSION_KEY] = [str(non_existent_uuid), str(company.pk)]
        session.save()

        merge_list_route_name = admin_urlname(Company._meta, 'merge-list')
        merge_list_url = reverse(merge_list_route_name)

        response = self.client.get(merge_list_url)

        assert response.status_code == status.HTTP_200_OK
        assert str(company.pk) in response.rendered_content
        assert str(non_existent_uuid) not in response.rendered_content

    def test_message_displayed_if_no_companies_added(self):
        """Test that a message is displayed if no companies are in the merge list."""
        merge_list_route_name = admin_urlname(Company._meta, 'merge-list')
        merge_list_url = reverse(merge_list_route_name)

        response = self.client.get(merge_list_url)

        assert response.status_code == status.HTTP_200_OK
        assert 'No companies have been added to the merge list.' in response.rendered_content

    def test_can_remove_a_company(self):
        """Test that a company can be removed from the merge list."""
        companies = CompanyFactory.create_batch(3)
        session = self.client.session
        session[MERGE_LIST_SESSION_KEY] = [str(company.pk) for company in companies]
        session.save()

        remove_route_name = admin_urlname(Company._meta, 'remove-from-merge-list')
        remove_url = reverse(remove_route_name, args=(companies[0].pk,))

        response = self.client.post(remove_url, follow=True)
        session = self.client.session

        assert response.status_code == status.HTTP_200_OK

        assert len(response.redirect_chain) == 1

        merge_list_route_name = admin_urlname(Company._meta, 'merge-list')
        merge_list_url = reverse(merge_list_route_name)

        assert response.redirect_chain[0][0] == merge_list_url
        assert session[MERGE_LIST_SESSION_KEY] == [str(company.pk) for company in companies[1:]]


class TestViewMergeListLink(AdminTestMixin):
    """Tests for the view merge list link on the change list page."""

    def test_link_is_not_displayed_if_no_items_in_merge_list(self):
        """
        Test that the 'View merge list' link is not displayed if there are no items in the list.
        """
        changelist_route_name = admin_urlname(Company._meta, 'changelist')
        changelist_url = reverse(changelist_route_name)

        response = self.client.get(changelist_url)

        merge_list_route_name = admin_urlname(Company._meta, 'merge-list')
        merge_list_url = reverse(merge_list_route_name)

        assert merge_list_url not in response.rendered_content

    def test_link_is_displayed_if_items_in_merge_list(self):
        """Test that the 'View merge list' link is displayed if there are items in the list."""
        company = CompanyFactory()
        session = self.client.session
        session[MERGE_LIST_SESSION_KEY] = [str(company.pk)]
        session.save()

        changelist_route_name = admin_urlname(Company._meta, 'changelist')
        changelist_url = reverse(changelist_route_name)

        response = self.client.get(changelist_url)

        merge_list_route_name = admin_urlname(Company._meta, 'merge-list')
        merge_list_url = reverse(merge_list_route_name)

        assert merge_list_url in response.rendered_content


class TestMergeListPermissions(AdminTestMixin):
    """Test permission handling in the merge list views."""

    @pytest.mark.parametrize(
        'route_name,needs_arg,method',
        (
            (
                admin_urlname(Company._meta, 'merge-list'),
                False,
                'get',
            ),
            (
                admin_urlname(Company._meta, 'add-to-merge-list'),
                True,
                'post',
            ),
            (
                admin_urlname(Company._meta, 'remove-from-merge-list'),
                True,
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
                admin_urlname(Company._meta, 'merge-list'),
                False,
                'get',
            ),
            (
                admin_urlname(Company._meta, 'add-to-merge-list'),
                True,
                'post',
            ),
            (
                admin_urlname(Company._meta, 'remove-from-merge-list'),
                True,
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
                admin_urlname(Company._meta, 'merge-list'),
                False,
                'get',
            ),
            (
                admin_urlname(Company._meta, 'add-to-merge-list'),
                True,
                'post',
            ),
            (
                admin_urlname(Company._meta, 'remove-from-merge-list'),
                True,
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
