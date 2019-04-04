from datetime import datetime
from unittest import mock
from uuid import uuid4

from django.contrib.admin.sites import site
from django.urls import reverse
from django.utils.timezone import now, utc
from freezegun import freeze_time

from datahub.company.test.factories import AdviserFactory
from datahub.core import constants
from datahub.core.test_utils import AdminTestMixin
from datahub.investment.project.admin import InvestmentProjectAdmin
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import InvestmentProjectFactory


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
        assert investment_project.gross_value_added == 6210

        # GVA Multiplier - Transportation & storage - 2019
        assert investment_project.gva_multiplier.multiplier == 0.0621
