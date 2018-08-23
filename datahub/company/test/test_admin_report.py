from datetime import datetime, timezone

import factory
import pytest
from django.conf import settings
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from datahub.company.admin_reports import AllAdvisersReport, OneListReport
from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core import constants
from datahub.core.test_utils import AdminTestMixin, create_test_user, random_obj_for_model
from datahub.metadata.models import CompanyClassification
from datahub.metadata.test.factories import TeamFactory

pytestmark = pytest.mark.django_db


class TestReportAdmin(AdminTestMixin):
    """Tests for the download of the report."""

    @freeze_time('2018-01-01 00:00:00')
    def test_adviser_report_download(self):
        """Test the download of a report."""
        AdviserFactory.create_batch(5)

        url = reverse('admin-report:download-report', kwargs={'report_id': 'all-advisers'})

        user = create_test_user(
            permission_codenames=('view_advisor',),
            is_staff=True,
            password=self.PASSWORD,
        )

        client = self.create_client(user=user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # 7 = header + test user + the 5 test advisers
        assert len(response.getvalue().decode('utf-8').splitlines()) == 7

    @freeze_time('2018-01-01 00:00:00')
    def test_one_list_download(self):
        """Test the download of the One List."""
        CompanyFactory.create_batch(
            2,
            headquarter_type_id=constants.HeadquarterType.ghq.value.id,
            classification=random_obj_for_model(CompanyClassification),
            one_list_account_owner=AdviserFactory(),
        )
        # ignored because headquarter_type is None
        CompanyFactory(
            headquarter_type=None,
            classification=random_obj_for_model(CompanyClassification),
            one_list_account_owner=AdviserFactory(),
        )
        # ignored because classification is None
        CompanyFactory(
            headquarter_type_id=constants.HeadquarterType.ghq.value.id,
            classification=None,
            one_list_account_owner=AdviserFactory(),
        )
        # ignored because one_list_account_owner is None
        CompanyFactory(
            headquarter_type_id=constants.HeadquarterType.ghq.value.id,
            classification=random_obj_for_model(CompanyClassification),
            one_list_account_owner=None,
        )

        url = reverse('admin-report:download-report', kwargs={'report_id': 'one-list'})

        user = create_test_user(
            permission_codenames=('view_company',),
            is_staff=True,
            password=self.PASSWORD,
        )

        client = self.create_client(user=user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # 3 = header + the first 2 companies
        assert len(response.getvalue().decode('utf-8').splitlines()) == 3


@freeze_time('2018-01-01 00:00:00')
def test_adviser_report_generation():
    """Test the generation of the report."""
    disabled_team = TeamFactory(
        disabled_on=datetime(1980, 1, 1, tzinfo=timezone.utc)
    )
    advisers = [
        AdviserFactory(date_joined=datetime(1980, 1, 1, tzinfo=timezone.utc)),
        AdviserFactory(date_joined=datetime(1990, 1, 1, tzinfo=timezone.utc), dit_team=None),
        AdviserFactory(
            date_joined=datetime(2000, 1, 1, tzinfo=timezone.utc),
            dit_team=disabled_team
        ),
    ]

    report = AllAdvisersReport()
    assert list(report.rows()) == [{
        'id': adviser.pk,
        'email': adviser.email,
        'name': adviser.name,
        'contact_email': adviser.contact_email,
        'is_active': adviser.is_active,
        'dit_team__name': adviser.dit_team.name if adviser.dit_team else None,
        'is_team_active': adviser.dit_team.disabled_on is None if adviser.dit_team else None,
        'dit_team__role__name': adviser.dit_team.role.name if adviser.dit_team else None,
    } for adviser in advisers]


def test_one_list_report_generation():
    """Test the generation of the One List."""
    companies = CompanyFactory.create_batch(
        2,
        headquarter_type_id=constants.HeadquarterType.ghq.value.id,
        classification=factory.Iterator(
            CompanyClassification.objects.all()  # keeps the ordering
        ),
        one_list_account_owner=AdviserFactory(),
    )
    # ignored because headquarter_type is None
    CompanyFactory(
        headquarter_type=None,
        classification=random_obj_for_model(CompanyClassification),
        one_list_account_owner=AdviserFactory(),
    )
    # ignored because classification is None
    CompanyFactory(
        headquarter_type_id=constants.HeadquarterType.ghq.value.id,
        classification=None,
        one_list_account_owner=AdviserFactory(),
    )
    # ignored because one_list_account_owner is None
    CompanyFactory(
        headquarter_type_id=constants.HeadquarterType.ghq.value.id,
        classification=random_obj_for_model(CompanyClassification),
        one_list_account_owner=None,
    )

    report = OneListReport()
    assert list(report.rows()) == [{
        'name': company.name,
        'classification__name': company.classification.name,
        'sector__segment': company.sector.segment,
        'primary_contact_name': company.one_list_account_owner.name,
        'one_list_account_owner__telephone_number':
            company.one_list_account_owner.telephone_number,
        'one_list_account_owner__contact_email': company.one_list_account_owner.contact_email,
        'registered_address_country__name': company.registered_address_country.name,
        'registered_address_town': company.registered_address_town,
        'url': f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["company"]}/{company.id}',
    } for company in companies]
