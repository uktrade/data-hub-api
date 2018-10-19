from urllib.parse import urlencode

import pytest
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from rest_framework import status

from datahub.company.models import Company, CompanyPermission
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import AdminTestMixin, create_test_user


@pytest.mark.usefixtures('merge_list_feature_flag')
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
        select_other_url = reverse(select_other_route_name, args=(company.pk,))

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
        select_other_url = reverse(select_other_route_name, args=(company.pk,))

        assert select_other_url not in response.rendered_content


@pytest.mark.usefixtures('merge_list_feature_flag')
class TestMergeWithAnotherCompanyView(AdminTestMixin):
    """Tests the 'merge with another company' form."""

    SAME_COMPANY = object()

    def test_proceeds_if_valid_company_provided(self):
        """Test the view redirects if a valid company is provided."""
        main_company = CompanyFactory()
        other_company = CompanyFactory()

        select_other_route_name = admin_urlname(Company._meta, 'merge-select-other-company')
        select_other_url = reverse(select_other_route_name, args=(main_company.pk,))

        response = self.client.get(
            select_other_url,
            follow=True,
            data={
                'other_company': str(other_company.pk),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1

        select_primary_route_name = admin_urlname(Company._meta, 'merge-select-primary-company')
        select_primary_url = reverse(select_primary_route_name)
        query_args = urlencode(
            {
                'company_1': main_company.pk,
                'company_2': other_company.pk,
            },
        )

        assert response.redirect_chain[0][0] == f'{select_primary_url}?{query_args}'

    @pytest.mark.parametrize(
        'other_company,expected_error',
        (
            (
                SAME_COMPANY,
                'The two companies to merge cannot be the same. Please select a different '
                'company.',
            ),
            (
                '1234',
                "'1234' is not a valid UUID.",
            ),
            (
                '',
                'This field is required.',
            ),
        ),
    )
    def test_error_if_invalid_company_selected(self, other_company, expected_error):
        """Test that an error is displayed if the an invalid company is selected."""
        company = CompanyFactory()

        select_other_route_name = admin_urlname(Company._meta, 'merge-select-other-company')
        select_other_url = reverse(select_other_route_name, args=(company.pk,))

        value = str(company.pk) if other_company is self.SAME_COMPANY else other_company

        response = self.client.get(
            select_other_url,
            data={
                'other_company': value,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        form = response.context['form']

        assert 'other_company' in form.errors
        assert form.errors['other_company'] == [expected_error]
