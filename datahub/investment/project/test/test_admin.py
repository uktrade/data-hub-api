from datetime import datetime
from decimal import Decimal
from unittest import mock
from uuid import uuid4

import pytest
from django.contrib.admin.sites import site
from django.urls import reverse
from django.utils.timezone import now, utc
from freezegun import freeze_time
from rest_framework import status

from datahub.company.test.factories import AdviserFactory
from datahub.core import constants
from datahub.core.test_utils import AdminTestMixin
from datahub.investment.project.admin import InvestmentProjectAdmin
from datahub.investment.project.constants import FDISICGrouping
from datahub.investment.project.models import GVAMultiplier, InvestmentProject
from datahub.investment.project.test.factories import (
    GVAMultiplierFactory,
    InvestmentProjectFactory,
)


@pytest.fixture
def get_gva_multiplier():
    """Get a GVA Multiplier for the year 3010"""
    yield GVAMultiplierFactory(
        financial_year=3010,
        fdi_sic_grouping_id=FDISICGrouping.retail.value.id,
        multiplier=2,
    )


class TestGVAMultiplierAdmin(AdminTestMixin):
    """Tests for GVA Multiplier django admin."""

    def test_adding_new_gva_multiplier(self):
        """Test adding a new GVA Multiplier."""
        url = reverse('admin:investment_gvamultiplier_add')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        multiplier_value = '0.12345'
        financial_year = 3015

        data = {
            'financial_year': financial_year,
            'multiplier': multiplier_value,
            'fdi_sic_grouping': str(FDISICGrouping.retail.value.id),
        }

        response = self.client.post(url, data, follow=True)
        assert response.status_code == status.HTTP_200_OK

        actual_multiplier = GVAMultiplier.objects.get(
            financial_year=financial_year,
            fdi_sic_grouping_id=FDISICGrouping.retail.value.id,
        )
        assert actual_multiplier.multiplier == Decimal(multiplier_value)

    @pytest.mark.parametrize(
        'data',
        (
            {
                'financial_year': 3011,
            },
            {
                'fdi_sic_grouping': str(FDISICGrouping.electric.value.id),
            },
        ),
    )
    def test_updating_gva_multiplier_group_and_year_not_allowed(self, get_gva_multiplier, data):
        """Test updating financial year and fdi sic grouping not allowed."""
        gva_multiplier = get_gva_multiplier
        url = reverse('admin:investment_gvamultiplier_change', args=(gva_multiplier.pk,))
        response = self.client.get(url, follow=True)
        assert response.status_code == status.HTTP_200_OK

        response = self.client.post(url, data, follow=True)
        assert response.status_code == status.HTTP_200_OK

        gva_multiplier.refresh_from_db()
        assert gva_multiplier.financial_year == 3010

    def test_updating_gva_multiplier_value(self, get_gva_multiplier):
        """Test updating GVA Multiplier value updates any associated investment projects."""
        gva_multiplier = get_gva_multiplier
        with mock.patch(
            'datahub.investment.project.gva_utils.'
            'GrossValueAddedCalculator._get_gva_multiplier',
        ) as mock_get_multiplier:
            mock_get_multiplier.return_value = gva_multiplier
            project = InvestmentProjectFactory(
                foreign_equity_investment=1000,
                investment_type_id=constants.InvestmentType.fdi.value.id,
            )

        url = reverse('admin:investment_gvamultiplier_change', args=(gva_multiplier.pk,))
        response = self.client.get(url, follow=True)
        assert response.status_code == status.HTTP_200_OK

        with mock.patch(
            'datahub.investment.project.gva_utils.'
            'GrossValueAddedCalculator._get_gva_multiplier_financial_year',
        ) as mock_get_financial_year:
            mock_get_financial_year.return_value = 3010

            data = {
                'multiplier': 3,
            }
            response = self.client.post(url, data, follow=True)
            assert response.status_code == status.HTTP_200_OK

        gva_multiplier.refresh_from_db()
        assert gva_multiplier.multiplier == 3

        project.refresh_from_db()
        assert project.gross_value_added == 3000


class TestInvestmentProjectAdmin(AdminTestMixin):
    """Tests for investment project django admin."""

    @freeze_time('2018-01-01 00:00:00')
    def test_if_assigning_project_manager_first_updates_related_columns(self):
        """
        Test that the assignment of project manager for the first time, updates who and when
        made an assignment.
        """
        investment_project = InvestmentProjectFactory()
        url = reverse('admin:investment_investmentproject_change', args=(investment_project.pk,))

        data = {}

        # populate data with required field values
        admin_form = InvestmentProjectAdmin(InvestmentProject, site).get_form(mock.Mock())
        for field_name, field in admin_form.base_fields.items():
            if field.required:
                field_value = getattr(investment_project, field_name)
                data[field_name] = field.prepare_value(field_value)

        project_manager = AdviserFactory()
        data['project_manager'] = project_manager.pk

        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200

        investment_project.refresh_from_db()
        assert investment_project.project_manager == project_manager
        assert investment_project.project_manager_first_assigned_on == now()
        assert investment_project.project_manager_first_assigned_by == self.user

    @freeze_time('2018-01-01 00:00:00')
    def test_if_assigning_project_manager_second_time_doesnt_update_related_columns(self):
        """
        Test that the assignment of project manager for the second time, doesn't update who and
        when made an assignment.
        """
        investment_project = InvestmentProjectFactory(
            project_manager=AdviserFactory(),
            project_manager_first_assigned_on=datetime(2010, 1, 2, 0, 0, tzinfo=utc),
            project_manager_first_assigned_by=AdviserFactory(),
        )
        url = reverse('admin:investment_investmentproject_change', args=(investment_project.pk,))

        data = {}

        # populate data with required field values
        admin_form = InvestmentProjectAdmin(InvestmentProject, site).get_form(mock.Mock())
        for field_name, field in admin_form.base_fields.items():
            if field.required:
                field_value = getattr(investment_project, field_name)
                data[field_name] = field.prepare_value(field_value)

        project_manager = AdviserFactory()
        data['project_manager'] = project_manager.pk

        response = self.client.post(url, data, follow=True)

        assert response.status_code == 200

        investment_project.refresh_from_db()
        assert investment_project.project_manager == project_manager
        assert investment_project.project_manager_first_assigned_on != now()
        assert investment_project.project_manager_first_assigned_by != self.user

    @freeze_time('2018-01-01 00:00:00')
    def test_if_assigning_project_manager_when_adding_updates_related_columns(self):
        """
        Test that the assignment of project manager for the first time, updates who and when
        made an assignment.
        """
        url = reverse('admin:investment_investmentproject_add')

        investment_project_pk = str(uuid4())
        project_manager = AdviserFactory()
        data = {
            'name': 'name 318',
            'description': 'desc 318',
            'investment_type': str(constants.InvestmentType.fdi.value.id),
            'stage': str(constants.InvestmentProjectStage.active.value.id),
            'status': 'ongoing',
            'project_manager': str(project_manager.pk),
            'proposal_deadline': '2017-04-19',
            'id': investment_project_pk,
        }
        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200

        investment_project = InvestmentProject.objects.get(pk=investment_project_pk)
        assert investment_project.project_manager == project_manager
        assert investment_project.project_manager_first_assigned_on == now()
        assert investment_project.project_manager_first_assigned_by == self.user

    @freeze_time('2018-01-01 00:00:00')
    def test_if_not_assigning_project_manager_when_adding_doesnt_update_related_columns(self):
        """Test that if project manager is not assigned, related columns are not updated."""
        url = reverse('admin:investment_investmentproject_add')

        investment_project_pk = str(uuid4())
        data = {
            'name': 'name 318',
            'description': 'desc 318',
            'investment_type': str(constants.InvestmentType.fdi.value.id),
            'stage': str(constants.InvestmentProjectStage.active.value.id),
            'status': 'ongoing',
            'proposal_deadline': '2017-04-19',
            'id': investment_project_pk,
        }
        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200

        investment_project = InvestmentProject.objects.get(pk=investment_project_pk)
        assert investment_project.project_manager is None
        assert investment_project.project_manager_first_assigned_on is None
        assert investment_project.project_manager_first_assigned_by is None

    @freeze_time('2018-01-01 00:00:00')
    def test_creating_project_sets_gross_value_added(self):
        """Test that gross value added is calculated when a project is created in admin."""
        url = reverse('admin:investment_investmentproject_add')

        investment_project_pk = str(uuid4())
        data = {
            'name': 'name 319',
            'description': 'desc 319',
            'investment_type': str(constants.InvestmentType.fdi.value.id),
            'id': investment_project_pk,
            'sector': str(constants.Sector.aerospace_assembly_aircraft.value.id),
            'foreign_equity_investment': 100000,
            'stage': str(constants.InvestmentProjectStage.active.value.id),
            'status': 'ongoing',
        }
        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200
        investment_project = InvestmentProject.objects.get(pk=investment_project_pk)
        assert investment_project.gross_value_added == Decimal('6210')

        # GVA Multiplier - Transportation & storage - 2019
        assert investment_project.gva_multiplier.multiplier == Decimal('0.0621')
