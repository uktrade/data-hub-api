import uuid

from datetime import datetime

import pytest

from dateutil.relativedelta import relativedelta

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import CompanyPermission
from datahub.company.test.factories import (
    CompanyFactory,
    ContactFactory,
)
from datahub.core.constants import (
    BreakdownType as BreakdownTypeConstant,
)
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_date_or_datetime,
)
from datahub.core.utils import get_financial_year
from datahub.export_win.test.factories import (
    BreakdownFactory,
    CustomerResponseFactory,
    WinFactory,
)


class TestGetCompanyExportWins(APITestMixin):
    """Test for GET endpoints that return export wins related to a company."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        company = CompanyFactory()
        url = reverse('api-v4:company:export-win', kwargs={'pk': company.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['view_company'], status.HTTP_403_FORBIDDEN),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status):
        """Test that a 403 is returned if the user has not enough permissions."""
        user = create_test_user(permission_codenames=permission_codenames)
        api_client = self.create_api_client(user=user)
        company = CompanyFactory()
        url = reverse('api-v4:company:export-win', kwargs={'pk': company.id})
        response = api_client.get(url)
        assert response.status_code == expected_status

    def test_no_company_with_pk_raises_404(self):
        """
        Test if company pk provided in get parameters doesn't match,
        404 is raised.
        """
        user = create_test_user(
            permission_codenames=(
                CompanyPermission.view_export_win,
            ),
        )
        api_client = self.create_api_client(user=user)
        dummy_company_id = uuid.uuid4()
        url = reverse('api-v4:company:export-win', kwargs={'pk': dummy_company_id})
        response = api_client.get(url)
        assert response.status_code == 404

    @pytest.mark.parametrize(
        'not_matched',
        (
            'lead_officer',
            'contact',
        ),
    )
    def test_get_export_wins_success(self, not_matched):
        """Test get wins in a successful scenario."""
        company = CompanyFactory()
        kwargs = {}
        if not_matched == 'lead_officer':
            kwargs.update({'lead_officer': None})
        if not_matched != 'contact':
            contact = ContactFactory(company=company)
            kwargs.update(
                {
                    'company_contacts': [contact],
                },
            )
        win = WinFactory(
            company=company,
            **kwargs,
        )
        breakdown = BreakdownFactory(
            type_id=BreakdownTypeConstant.export.value.id,
            win=win,
        )
        customer_response = CustomerResponseFactory(
            win=win,
            responded_on=datetime.utcnow(),
            agree_with_win=True,
        )
        financial_year = get_financial_year(
            breakdown.win.date + relativedelta(years=breakdown.year - 1),
        )
        if not_matched == 'lead_officer':
            officer = {
                'name': win.lead_officer_name,
                'email': win.lead_officer_email_address,
                'team': {
                    'type': win.team_type.name,
                    'sub_type': win.hq_team.name,
                },
            }
        else:
            officer = {
                'name': win.lead_officer.name,
                'email': win.lead_officer.contact_email,
                'team': {
                    'type': win.team_type.name,
                    'sub_type': win.hq_team.name,
                },
            }
        if not_matched == 'contact':
            contact = {
                'name': win.customer_name,
                'email': win.customer_email_address,
                'job_title': win.customer_job_title,
            }
        else:
            company_contact = win.company_contacts.first()
            contact = {
                'name': company_contact.name,
                'email': company_contact.email,
                'job_title': company_contact.job_title,
            }

        export_wins_response = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': str(win.id),
                    'date': format_date_or_datetime(win.date),
                    'created': format_date_or_datetime(win.created_on),
                    'country': win.country.iso_alpha2_code,
                    'sector': win.sector.name,
                    'business_potential': win.business_potential.export_win_id,
                    'business_type': win.business_type,
                    'name_of_export': win.name_of_export,
                    # this field is intentionally duplicated to match legacy system output
                    'title': win.name_of_export,
                    'officer': officer,
                    'contact': contact,
                    'value': {
                        'export': {
                            'total': win.total_expected_export_value,
                            'breakdowns': [{
                                'year': financial_year,
                                'value': breakdown.value,
                            }],
                        },
                    },
                    'customer': win.company_name,
                    'response': {
                        'confirmed': customer_response.agree_with_win,
                        'date': format_date_or_datetime(customer_response.responded_on),
                    },
                    'hvc': {
                        'code': win.hvc.campaign_id,
                        'name': win.hvc.name,
                    },
                },
            ],
        }

        user = create_test_user(
            permission_codenames=(
                CompanyPermission.view_export_win,
            ),
        )
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:company:export-win', kwargs={'pk': company.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json() == export_wins_response
