from datetime import datetime, timezone
from decimal import Decimal
from unittest import mock
from uuid import UUID, uuid4

import pytest
from django.contrib.admin.sites import site
from django.urls import reverse
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status

from datahub.company.test.factories import AdviserFactory
from datahub.core import constants
from datahub.core.test_utils import AdminTestMixin
from datahub.investment.project.admin import InvestmentProjectAdmin
from datahub.investment.project.constants import (
    FDISICGrouping as FDISICGroupingConstant,
)

from datahub.investment.project.models import (
    GVAMultiplier,
    InvestmentProject,
)
from datahub.investment.project.test.factories import (
    GVAMultiplierFactory,
    InvestmentProjectFactory,
)


DEFAULT_SECTOR_ID = constants.Sector.renewable_energy_wind.value.id
DEFAULT_FDI_SIC_GROUPING_ID = FDISICGroupingConstant.electric.value.id
DEFAULT_MULTIPLIER = Decimal('2.0')

ALTERNATE_SECTOR_ID = constants.Sector.mining_mining_vehicles_transport_equipment.value.id
ALTERNATE_FDI_SIC_GROUPING_ID = FDISICGroupingConstant.mining.value.id
ALTERNATE_MULTIPLIER = Decimal('0.5')

CAPITAL = GVAMultiplier.SectorClassificationChoices.CAPITAL
LABOUR = GVAMultiplier.SectorClassificationChoices.LABOUR


@pytest.fixture
def get_gva_multiplier():
    """Get a GVA Multiplier for the year 3010"""
    yield GVAMultiplierFactory(
        multiplier=DEFAULT_MULTIPLIER,
        financial_year=3010,
        sector_id=DEFAULT_SECTOR_ID,
        sector_classification_gva_multiplier=CAPITAL,
        sector_classification_value_band=CAPITAL,
        fdi_sic_grouping_id=DEFAULT_FDI_SIC_GROUPING_ID,
    )


class TestGVAMultiplierAdmin(AdminTestMixin):
    """Tests for GVA Multiplier django admin."""

    def test_adding_new_gva_multiplier(self):
        """Test adding a new GVA Multiplier."""
        url = reverse('admin:investment_gvamultiplier_add')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        multiplier = DEFAULT_MULTIPLIER
        financial_year = 3015
        sector_id = DEFAULT_SECTOR_ID
        sector_classification_gva_multiplier = CAPITAL
        sector_classification_value_band = CAPITAL
        fdi_sic_grouping_id = DEFAULT_FDI_SIC_GROUPING_ID
        value_band_a_minimum = 1
        value_band_b_minimum = 2
        value_band_c_minimum = 3
        value_band_d_minimum = 4
        value_band_e_minimum = 5

        data = {
            'multiplier': multiplier,
            'financial_year': financial_year,
            'sector': sector_id,
            'sector_classification_gva_multiplier': sector_classification_gva_multiplier,
            'sector_classification_value_band': sector_classification_value_band,
            'fdi_sic_grouping': fdi_sic_grouping_id,
            'value_band_a_minimum': value_band_a_minimum,
            'value_band_b_minimum': value_band_b_minimum,
            'value_band_c_minimum': value_band_c_minimum,
            'value_band_d_minimum': value_band_d_minimum,
            'value_band_e_minimum': value_band_e_minimum,
        }

        response = self.client.post(url, data, follow=True)
        assert response.status_code == status.HTTP_200_OK

        actual_multiplier = GVAMultiplier.objects.get(
            financial_year=financial_year,
            sector=sector_id,
        )
        assert actual_multiplier.multiplier == Decimal(multiplier)

    @pytest.mark.parametrize(
        'data',
        (
            {
                'multiplier': ALTERNATE_MULTIPLIER,
            },
            {
                'financial_year': 3011,
            },
            {
                'sector': ALTERNATE_SECTOR_ID,
            },
            {
                'sector_classification_gva_multiplier': LABOUR,
            },
            {
                'sector_classification_value_band': LABOUR,
            },
            {
                'value_band_a_minimum': 10,
            },
            {
                'value_band_b_minimum': 20,
            },
            {
                'value_band_c_minimum': 30,
            },
            {
                'value_band_d_minimum': 40,
            },
            {
                'value_band_e_minimum': 50,
            },
            {
                'fdi_sic_grouping': ALTERNATE_FDI_SIC_GROUPING_ID,
            },
        ),
    )
    def test_updating_gva_multiplier_not_allowed(self, get_gva_multiplier, data):
        """Test updating GVA multiplier not allowed."""
        gva_multiplier = get_gva_multiplier
        url = reverse('admin:investment_gvamultiplier_change', args=(gva_multiplier.pk,))
        response = self.client.get(url, follow=True)
        assert response.status_code == status.HTTP_200_OK

        response = self.client.post(url, data, follow=True)
        assert response.status_code == status.HTTP_200_OK

        gva_multiplier.refresh_from_db()
        assert gva_multiplier.multiplier == DEFAULT_MULTIPLIER
        assert gva_multiplier.financial_year == 3010
        assert gva_multiplier.sector_id == UUID(DEFAULT_SECTOR_ID)
        assert gva_multiplier.sector_classification_gva_multiplier == CAPITAL
        assert gva_multiplier.sector_classification_value_band == CAPITAL
        assert gva_multiplier.fdi_sic_grouping_id == UUID(DEFAULT_FDI_SIC_GROUPING_ID)
        # these should match those specified in the GVAMultiplerFactory
        assert gva_multiplier.value_band_a_minimum == 2
        assert gva_multiplier.value_band_b_minimum == 4
        assert gva_multiplier.value_band_c_minimum == 8
        assert gva_multiplier.value_band_d_minimum == 16
        assert gva_multiplier.value_band_e_minimum == 32


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
        assert response.status_code == status.HTTP_200_OK

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
            project_manager_first_assigned_on=datetime(2010, 1, 2, 0, 0, tzinfo=timezone.utc),
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

        assert response.status_code == status.HTTP_200_OK

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
        assert response.status_code == status.HTTP_200_OK

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
        assert response.status_code == status.HTTP_200_OK

        investment_project = InvestmentProject.objects.get(pk=investment_project_pk)
        assert investment_project.project_manager is None
        assert investment_project.project_manager_first_assigned_on is None
        assert investment_project.project_manager_first_assigned_by is None

    def test_add_investment_project_view_returns_200_response(self):
        """Test that add investment project returns HTTP 200 OK."""
        url = reverse('admin:investment_investmentproject_add')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

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
        assert investment_project.gross_value_added == Decimal('20965')

        # GVA Multiplier - Aircraft - 2022
        assert investment_project.gva_multiplier.multiplier == Decimal('0.209650945')
