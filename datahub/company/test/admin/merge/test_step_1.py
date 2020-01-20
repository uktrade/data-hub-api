import pytest
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from rest_framework import status

from datahub.company.models import Company, CompanyPermission
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import AdminTestMixin, create_test_user
from datahub.core.utils import reverse_with_query_string


class TestMergeWithAnotherCompanyLink(AdminTestMixin):
    """Tests the 'merge with another company' link on the change form."""

    def test_link_exists(self):
        """Test that the link exists for a user with the change company permission."""
        company = CompanyFactory()

        change_route_name = admin_urlname(Company._meta, 'change')
        change_url = reverse(change_route_name, args=(company.pk,))

        response = self.client.get(change_url)
        assert response.status_code == status.HTTP_200_OK

        select_other_route_name = admin_urlname(Company._meta, 'merge-select-other-company')
        select_other_query_args = {
            'company_1': company.pk,
        }
        select_other_url = reverse_with_query_string(
            select_other_route_name,
            select_other_query_args,
        )

        assert select_other_url in response.rendered_content

    def test_link_does_not_exist_with_only_view_permission(self):
        """Test that the link does not exist for a user with only the view company permission."""
        company = CompanyFactory()

        change_route_name = admin_urlname(Company._meta, 'change')
        change_url = reverse(change_route_name, args=(company.pk,))

        user = create_test_user(
            permission_codenames=(CompanyPermission.view_company,),
            is_staff=True,
            password=self.PASSWORD,
        )
        client = self.create_client(user=user)
        response = client.get(change_url)
        assert response.status_code == status.HTTP_200_OK

        select_other_route_name = admin_urlname(Company._meta, 'merge-select-other-company')
        select_other_url = reverse(select_other_route_name)

        assert select_other_url not in response.rendered_content


class TestMergeWithAnotherCompanyViewGet(AdminTestMixin):
    """Tests GET requests for the 'Merge with another company' view."""

    @pytest.mark.parametrize(
        'data',
        (
            {},
            {
                'company_1': '',
            },
            {
                'company_1': '12345',
            },
        ),
    )
    def test_returns_400_if_invalid_company_passed(self, data):
        """
        Test that a 400 is returned when an invalid value is passed in the query string.

        This could only happen if the query string was manipulated, or the referenced company
        was deleted.
        """
        select_other_route_name = admin_urlname(Company._meta, 'merge-select-other-company')
        select_other_url = reverse(select_other_route_name)

        response = self.client.get(select_other_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_200_if_valid_companies_passed(self):
        """Tests that a 200 is returned if a valid company is passed in the query string."""
        company_1 = CompanyFactory()

        select_other_route_name = admin_urlname(Company._meta, 'merge-select-other-company')
        select_other_url = reverse(select_other_route_name)

        response = self.client.get(
            select_other_url,
            data={
                'company_1': str(company_1.pk),
            },
        )

        assert response.status_code == status.HTTP_200_OK


class TestMergeWithAnotherCompanyViewPost(AdminTestMixin):
    """Tests form submission for the 'Merge with another company' view."""

    SAME_COMPANY = object()

    def test_proceeds_if_valid_company_provided(self):
        """Test the view redirects if a valid company is provided."""
        main_company = CompanyFactory()
        other_company = CompanyFactory()

        select_other_route_name = admin_urlname(Company._meta, 'merge-select-other-company')
        select_other_query_args = {
            'company_1': main_company.pk,
        }
        select_other_url = reverse_with_query_string(
            select_other_route_name,
            select_other_query_args,
        )

        response = self.client.post(
            select_other_url,
            follow=True,
            data={
                'company_2': str(other_company.pk),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1

        select_primary_route_name = admin_urlname(Company._meta, 'merge-select-primary-company')
        select_primary_query_args = {
            'company_1': main_company.pk,
            'company_2': other_company.pk,
        }
        select_primary_url = reverse_with_query_string(
            select_primary_route_name,
            select_primary_query_args,
        )

        assert response.redirect_chain[0][0] == select_primary_url

    @pytest.mark.parametrize(
        'company_2,expected_error',
        (
            (
                SAME_COMPANY,
                'The two companies to merge cannot be the same. Please select a different '
                'company.',
            ),
            (
                '1234',
                '“1234” is not a valid UUID.',
            ),
            (
                '',
                'This field is required.',
            ),
        ),
    )
    def test_error_if_invalid_company_selected(self, company_2, expected_error):
        """Test that an error is displayed if the an invalid company is selected."""
        company = CompanyFactory()

        select_other_route_name = admin_urlname(Company._meta, 'merge-select-other-company')
        select_other_query_args = {
            'company_1': company.pk,
        }
        select_other_url = reverse_with_query_string(
            select_other_route_name,
            select_other_query_args,
        )

        value = str(company.pk) if company_2 is self.SAME_COMPANY else company_2

        response = self.client.post(
            select_other_url,
            data={
                'company_2': value,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        form = response.context['form']

        assert 'company_2' in form.errors
        assert form.errors['company_2'] == [expected_error]
