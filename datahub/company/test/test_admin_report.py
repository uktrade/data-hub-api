from datetime import datetime, timezone

import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from datahub.company.admin_reports import AllAdvisersReport
from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import AdminTestMixin, create_test_user
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
            permission_codenames=('read_advisor',),
            is_staff=True,
            password=self.PASSWORD,
        )

        client = self.create_client(user=user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # 7 = header + test user + the 5 test advisers
        assert len(response.getvalue().decode('utf-8').splitlines()) == 7


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
