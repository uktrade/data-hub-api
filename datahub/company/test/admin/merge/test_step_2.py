import pytest
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import NON_FIELD_ERRORS
from django.test.html import parse_html
from django.urls import reverse
from rest_framework import status

from datahub.company.models import Company
from datahub.company.test.factories import (
    ArchivedCompanyFactory,
    CompanyFactory,
    SubsidiaryFactory,
)
from datahub.core.test_utils import AdminTestMixin
from datahub.core.utils import reverse_with_query_string
from datahub.omis.order.test.factories import OrderFactory


class TestSelectPrimaryCompanyViewGet(AdminTestMixin):
    """Tests form rendering in the 'Select primary company' view."""

    @pytest.mark.parametrize(
        'data',
        (
            {},
            {
                'company_1': '12345',
                'company_2': '64567',
            },
            {
                'company_1': '',
                'company_2': '',
            },
            {
                'company_1': '12345',
            },
            {
                'company_1': lambda: str(CompanyFactory().pk),
                'company_2': '64567',
            },
            {
                'company_1': '13495',
                'company_2': lambda: str(CompanyFactory().pk),
            },
        ),
    )
    def test_returns_400_if_invalid_companies_passed(self, data):
        """
        Test that a 400 is returned when invalid values are passed for company_1 or company_2.

        This could only happen if the query string was manipulated, or one of the referenced
        companies was deleted.
        """
        for key, value in data.items():
            if callable(value):
                data[key] = value()

        select_primary_route_name = admin_urlname(Company._meta, 'merge-select-primary-company')
        select_primary_url = reverse(select_primary_route_name)

        response = self.client.get(select_primary_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        'swap', (True, False),
    )
    @pytest.mark.parametrize(
        'company_1_factory,company_2_factory',
        (
            (
                ArchivedCompanyFactory,
                CompanyFactory,
            ),
            (
                CompanyFactory,
                lambda: OrderFactory().company,
            ),
            (
                CompanyFactory,
                SubsidiaryFactory,
            ),
            (
                CompanyFactory,
                lambda: SubsidiaryFactory().global_headquarters,
            ),
        ),
        ids=[
            'archived-company',
            'company-with-order',
            'subsidiary',
            'global-headquarters',
        ],
    )
    def test_radio_button_correctly_enabled_or_disabled(
        self,
        company_1_factory,
        company_2_factory,
        swap,
    ):
        """
        Tests that the radio button to select a company is disabled if it is archived,
        or the other company has an OMIS order or other related object
        (other than an interaction, contact or investment project).
        """
        company_1 = (company_2_factory if swap else company_1_factory)()
        company_2 = (company_1_factory if swap else company_2_factory)()
        company_1_disabled = not swap
        company_2_disabled = swap

        select_primary_route_name = admin_urlname(Company._meta, 'merge-select-primary-company')
        select_primary_url = reverse(select_primary_route_name)

        response = self.client.get(
            select_primary_url,
            data={
                'company_1': str(company_1.pk),
                'company_2': str(company_2.pk),
            },
        )

        assert response.status_code == status.HTTP_200_OK

        expected_radio_1_html = _get_radio_html(1, company_1_disabled)
        assert _html_count_occurrences(expected_radio_1_html, response.rendered_content) == 1

        expected_radio_2_html = _get_radio_html(2, company_2_disabled)
        assert _html_count_occurrences(expected_radio_2_html, response.rendered_content) == 1


class TestSelectPrimaryCompanyViewPost(AdminTestMixin):
    """Tests form submission in the 'Select primary company' view."""

    @pytest.mark.parametrize('selected_company', ('1', '2'))
    def test_proceeds_if_company_chosen(self, selected_company):
        """Test that if a valid selection is made, the user is redirected to the change list."""
        company_1 = CompanyFactory()
        company_2 = CompanyFactory()

        select_primary_route_name = admin_urlname(Company._meta, 'merge-select-primary-company')
        select_primary_query_args = {
            'company_1': str(company_1.pk),
            'company_2': str(company_2.pk),
        }
        select_primary_url = reverse_with_query_string(
            select_primary_route_name,
            select_primary_query_args,
        )

        response = self.client.post(
            select_primary_url,
            follow=True,
            data={
                'selected_company': selected_company,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1

        confirm_merge_route_name = admin_urlname(Company._meta, 'merge-confirm')
        confirm_merge_query_args = {
            'source_company': (company_1 if selected_company != '1' else company_2).pk,
            'target_company': (company_1 if selected_company == '1' else company_2).pk,
        }
        confirm_merge_url = reverse_with_query_string(
            confirm_merge_route_name,
            confirm_merge_query_args,
        )

        assert response.redirect_chain[0][0] == confirm_merge_url

    @pytest.mark.parametrize('swap', (False, True))
    @pytest.mark.parametrize(
        'company_1_factory,company_2_factory,expected_error',
        (
            (
                ArchivedCompanyFactory,
                CompanyFactory,
                'The company selected is archived.',
            ),
            (
                CompanyFactory,
                lambda: OrderFactory().company,
                'The other company has related records which can’t be moved to the selected '
                'company.',
            ),
            (
                CompanyFactory,
                SubsidiaryFactory,
                'The other company has related records which can’t be moved to the selected '
                'company.',
            ),
            (
                CompanyFactory,
                lambda: SubsidiaryFactory().global_headquarters,
                'The other company has related records which can’t be moved to the selected '
                'company.',
            ),
        ),
    )
    def test_error_displayed_if_invalid_selection_made(
        self,
        swap,
        company_1_factory,
        company_2_factory,
        expected_error,
    ):
        """Tests that if an invalid selection is submitted, an error is returned."""
        company_1 = (company_2_factory if swap else company_1_factory)()
        company_2 = (company_1_factory if swap else company_2_factory)()
        selected_company = 2 if swap else 1

        select_primary_route_name = admin_urlname(Company._meta, 'merge-select-primary-company')
        select_primary_query_args = {
            'company_1': str(company_1.pk),
            'company_2': str(company_2.pk),
        }
        select_primary_url = reverse_with_query_string(
            select_primary_route_name,
            select_primary_query_args,
        )

        response = self.client.post(
            select_primary_url,
            data={
                'company_1': str(company_1.pk),
                'company_2': str(company_2.pk),
                'selected_company': selected_company,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        form = response.context['form']
        assert form.errors == {
            NON_FIELD_ERRORS: [expected_error],
        }


def _get_radio_html(index, disabled):
    extra_attrs = ' disabled' if disabled else ''
    return f"""<input name="selected_company" value="{index}" required="" \
id="id_selected_company_radio_{index}" type="radio" {extra_attrs}>"""


def _html_count_occurrences(needle, haystack):
    parsed_haystack = parse_html(haystack)
    parsed_needle = parse_html(needle)
    return parsed_haystack.count(parsed_needle)
