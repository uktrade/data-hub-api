from datetime import date

import pytest

from datahub.core.constants import FDIValue
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.mi_dashboard.models import MIInvestmentProject
from datahub.mi_dashboard.pipelines import (
    ETLInvestmentProjects,
    ETLInvestmentProjectsFinancialYear,
    run_mi_investment_project_etl_pipeline,
)
from datahub.mi_dashboard.query_utils import (
    NO_FDI_VALUE_ASSIGNED,
)

pytestmark = pytest.mark.django_db


def test_load_investment_projects():
    """Tests that investment projects are loaded to FDIDashboard table."""
    InvestmentProjectFactory.create_batch(10)
    etl = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = etl.load()
    assert (0, 10) == (updated, created)

    dashboard = MIInvestmentProject.objects.values(*etl.COLUMNS).all()
    for row in dashboard:
        source_row = etl.get_rows().get(pk=row['dh_fdi_project_id'])
        assert source_row == row


def test_investment_projects_get_updated():
    """Tests that investment projects get updated when running load again."""
    investment_projects = InvestmentProjectFactory.create_batch(10)
    extract = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = extract.load()
    assert (0, 10) == (updated, created)

    dashboard = MIInvestmentProject.objects.values(*extract.COLUMNS).all()
    for row in dashboard:
        source_row = extract.get_rows().get(pk=row['dh_fdi_project_id'])
        assert source_row == row

    for investment_project in investment_projects:
        investment_project.number_new_jobs = 100000000
        investment_project.save()

    updated, created = extract.load()
    assert (10, 0) == (updated, created)

    dashboard = MIInvestmentProject.objects.values(*extract.COLUMNS).all()
    for row in dashboard:
        source_row = extract.get_rows().get(pk=row['dh_fdi_project_id'])
        assert row['number_new_jobs'] == 100000000
        assert source_row == row


def test_load_investment_projects_2018_2019():
    """
    Tests that investment projects for financial year 2018/2019 are loaded to FDIDashboard table.
    """
    InvestmentProjectFactory.create_batch(5, actual_land_date=None, estimated_land_date=None)
    InvestmentProjectFactory.create_batch(5, actual_land_date=date(2014, 2, 3))
    InvestmentProjectFactory.create_batch(5, actual_land_date=date(2019, 4, 2))
    etl = ETLInvestmentProjectsFinancialYear(
        destination=MIInvestmentProject,
        financial_year='2018/2019',
    )

    updated, created = etl.load()
    assert (0, 5) == (updated, created)

    dashboard = MIInvestmentProject.objects.values(*etl.COLUMNS).all()
    for row in dashboard:
        source_row = etl.get_rows().get(pk=row['dh_fdi_project_id'])
        assert source_row['financial_year'] == '2018/2019'
        assert source_row == row


def test_run_mi_investment_project_etl_pipeline():
    """Tests that run_mi_investment_project_etl_pipeline copy data to FDIDashboard table."""
    InvestmentProjectFactory.create_batch(5, actual_land_date=date(2018, 4, 6))
    InvestmentProjectFactory.create_batch(5, actual_land_date=date(2018, 4, 5))

    financial_year = '2018/2019'

    updated, created = run_mi_investment_project_etl_pipeline(financial_year)
    assert (0, 5) == (updated, created)

    etl = ETLInvestmentProjects(destination=MIInvestmentProject)
    dashboard = MIInvestmentProject.objects.values(*ETLInvestmentProjects.COLUMNS).all()
    for row in dashboard:
        source_row = etl.get_rows().get(pk=row['dh_fdi_project_id'])
        assert source_row['financial_year'] == financial_year
        assert source_row == row


@pytest.mark.parametrize(
    'fdi_value_id,expected',
    (
        (FDIValue.higher.value.id, FDIValue.higher.value.name),
        (None, NO_FDI_VALUE_ASSIGNED),
    ),
)
def test_project_fdi_value(fdi_value_id, expected):
    """Tests that investment projects are loaded to FDIDashboard table."""
    InvestmentProjectFactory(
        fdi_value_id=fdi_value_id,
    )
    etl = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = etl.load()
    assert (0, 1) == (updated, created)

    mi_investment_project = MIInvestmentProject.objects.values(*etl.COLUMNS).first()
    assert mi_investment_project['project_fdi_value'] == expected
