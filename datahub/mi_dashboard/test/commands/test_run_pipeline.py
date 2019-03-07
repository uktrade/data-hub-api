import pytest
from django.core import management

from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.mi_dashboard.management.commands import run_pipeline
from datahub.mi_dashboard.models import MIInvestmentProject
from datahub.mi_dashboard.pipelines import ETLInvestmentProjects

# mark the whole module for db use
pytestmark = pytest.mark.django_db


def test_run_pipeline(caplog):
    """Tests that run_pipeline command copy investment projects to MIInvestmentProject table."""
    caplog.set_level('INFO')

    InvestmentProjectFactory.create_batch(5)

    management.call_command(run_pipeline.Command())

    assert 'Updated "0" and created "5" investment projects.' in caplog.text
    assert len(caplog.records) == 1

    etl = ETLInvestmentProjects(destination=MIInvestmentProject)
    dashboard = MIInvestmentProject.objects.values(*ETLInvestmentProjects.COLUMNS)
    for row in dashboard:
        source_row = etl.get_rows().get(pk=row['dh_fdi_project_id'])
        assert source_row == row
