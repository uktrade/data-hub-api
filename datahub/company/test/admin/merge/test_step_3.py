import pytest
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from rest_framework import status

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import AdminTestMixin
from datahub.core.utils import reverse_with_query_string


@pytest.mark.usefixtures('merge_list_feature_flag')
class TestConfirmMergeViewGet(AdminTestMixin):
    """Tests GET requests for the 'Confirm merge' view."""

    @pytest.mark.parametrize(
        'data',
        (
            {},
            {
                'source_company': '12345',
                'target_company': '64567',
            },
            {
                'source_company': '',
                'target_company': '',
            },
            {
                'source_company': '12345',
            },
            {
                'source_company': lambda: str(CompanyFactory().pk),
                'target_company': '64567',
            },
            {
                'source_company': '13495',
                'target_company': lambda: str(CompanyFactory().pk),
            },
        ),
    )
    def test_returns_400_if_invalid_companies_passed(self, data):
        """
        Test that a 400 is returned when invalid values are passed in the query string.

        This could only happen if the query string was manipulated, or one of the referenced
        companies was deleted.
        """
        for key, value in data.items():
            if callable(value):
                data[key] = value()

        confirm_merge_route_name = admin_urlname(Company._meta, 'merge-confirm')
        confirm_merge_url = reverse(confirm_merge_route_name)

        response = self.client.get(confirm_merge_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_200_if_valid_companies_passed(self):
        """Tests that a 200 is returned if valid companies are passed in the query string."""
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        confirm_merge_route_name = admin_urlname(Company._meta, 'merge-confirm')
        confirm_merge_url = reverse(confirm_merge_route_name)

        response = self.client.get(
            confirm_merge_url,
            data={
                'source_company': str(source_company.pk),
                'target_company': str(target_company.pk),
            },
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.usefixtures('merge_list_feature_flag')
class TestConfirmMergeViewPost(AdminTestMixin):
    """Tests form submission in the 'Confirm merge' view."""

    def test_proceeds_on_button_click(self):
        """Test that if a valid selection is made, the user is redirected to the change list."""
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        confirm_merge_route_name = admin_urlname(Company._meta, 'merge-confirm')
        confirm_merge_query_args = {
            'source_company': str(source_company.pk),
            'target_company': str(target_company.pk),
        }
        confirm_merge_url = reverse_with_query_string(
            confirm_merge_route_name,
            confirm_merge_query_args,
        )

        response = self.client.post(
            confirm_merge_url,
            follow=True,
            data={},
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1

        changelist_route_name = admin_urlname(Company._meta, 'changelist')
        changelist_url = reverse(changelist_route_name)

        assert response.redirect_chain[0][0] == changelist_url
