from datetime import date

import pytest
from django.conf import settings

from datahub.company.test.factories import CompanyFactory
from datahub.core.constants import Country, FDIValue, Sector, SectorCluster, UKRegion
from datahub.dbmaintenance.utils import parse_uuid
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import SectorFactory
from datahub.mi_dashboard.constants import (
    NO_FDI_VALUE_ASSIGNED,
    NO_SECTOR_ASSIGNED,
    NO_SECTOR_CLUSTER_ASSIGNED,
    NO_UK_REGION_ASSIGNED,
)
from datahub.mi_dashboard.models import MIInvestmentProject
from datahub.mi_dashboard.pipelines import (
    ETLInvestmentProjects,
    ETLInvestmentProjectsFinancialYear,
    run_mi_investment_project_etl_pipeline,
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
    InvestmentProjectFactory.create_batch(5, actual_land_date=date(2019, 3, 28))
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
    InvestmentProjectFactory.create_batch(5, actual_land_date=date(2018, 4, 1))
    InvestmentProjectFactory.create_batch(5, actual_land_date=date(2018, 3, 31))

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
    """Tests that project fdi value gets default value when fdi value is null."""
    InvestmentProjectFactory(
        fdi_value_id=fdi_value_id,
    )
    etl = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = etl.load()
    assert (0, 1) == (updated, created)

    mi_investment_project = MIInvestmentProject.objects.values(*etl.COLUMNS).first()
    assert mi_investment_project['project_fdi_value'] == expected


@pytest.mark.parametrize(
    'country_id,expected',
    (
        (Country.canada.value.id, Country.canada.value.name),
        (None, ''),
    ),
)
def test_investor_company_country(country_id, expected):
    """Tests that if investor country is not set investor_company_country is empty."""
    investor_company = CompanyFactory(
        registered_address_country_id=country_id,
    )
    InvestmentProjectFactory(
        investor_company=investor_company,
    )
    etl = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = etl.load()
    assert (0, 1) == (updated, created)

    mi_investment_project = MIInvestmentProject.objects.values(*etl.COLUMNS).first()
    assert mi_investment_project['investor_company_country'] == expected


@pytest.mark.parametrize(
    'country_id',
    (
        Country.canada.value.id,
        None,
    ),
)
def test_country_url(country_id):
    """Tests that if investor country is not set country url is empty."""
    investor_company = CompanyFactory(
        registered_address_country_id=country_id,
    )
    InvestmentProjectFactory(
        investor_company=investor_company,
    )
    etl = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = etl.load()
    assert (0, 1) == (updated, created)

    if country_id is None:
        expected = ''
    else:
        key = 'mi_fdi_dashboard_country'
        expected = f'{settings.DATAHUB_FRONTEND_URL_PREFIXES[key]}{country_id}'

    mi_investment_project = MIInvestmentProject.objects.values(*etl.COLUMNS).first()
    assert mi_investment_project['country_url'] == expected


@pytest.mark.parametrize(
    'total_investment,expected',
    (
        (10000, 10000),
        (0, 0),
        (None, 0),
    ),
)
def test_total_investment(total_investment, expected):
    """Tests that total investment with zero is zero when source value is null."""
    InvestmentProjectFactory(
        total_investment=total_investment,
    )
    etl = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = etl.load()
    assert (0, 1) == (updated, created)

    mi_investment_project = MIInvestmentProject.objects.values(*etl.COLUMNS).first()
    assert mi_investment_project['total_investment'] == total_investment
    assert mi_investment_project['total_investment_with_zero'] == expected


@pytest.mark.parametrize(
    'number_safeguarded_jobs,expected',
    (
        (10000, 10000),
        (0, 0),
        (None, 0),
    ),
)
def test_number_safeguarded_jobs(number_safeguarded_jobs, expected):
    """Tests that number safeguarded jobs with zero is zero when source value is null."""
    InvestmentProjectFactory(
        number_safeguarded_jobs=number_safeguarded_jobs,
    )
    etl = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = etl.load()
    assert (0, 1) == (updated, created)

    mi_investment_project = MIInvestmentProject.objects.values(*etl.COLUMNS).first()
    assert mi_investment_project['number_safeguarded_jobs'] == number_safeguarded_jobs
    assert mi_investment_project['number_safeguarded_jobs_with_zero'] == expected


@pytest.mark.parametrize(
    'number_new_jobs,expected',
    (
        (10000, 10000),
        (0, 0),
        (None, 0),
    ),
)
def test_number_new_jobs(number_new_jobs, expected):
    """Tests that number new jobs with zero is zero when source value is null."""
    InvestmentProjectFactory(
        number_new_jobs=number_new_jobs,
    )
    etl = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = etl.load()
    assert (0, 1) == (updated, created)

    mi_investment_project = MIInvestmentProject.objects.values(*etl.COLUMNS).first()
    assert mi_investment_project['number_new_jobs'] == number_new_jobs
    assert mi_investment_project['number_new_jobs_with_zero'] == expected


@pytest.mark.parametrize(
    'actual_land_date,estimated_land_date,expected_land_date',
    (
        (date(2015, 4, 2), None, date(2015, 4, 2)),
        (None, None, None),
        (None, date(2018, 9, 29), date(2018, 9, 29)),
        (date(2015, 2, 14), date(2018, 9, 29), date(2015, 2, 14)),
    ),
)
def test_land_date(actual_land_date, estimated_land_date, expected_land_date):
    """Tests that land date becomes either actual land date or estimated land date."""
    InvestmentProjectFactory(
        actual_land_date=actual_land_date,
        estimated_land_date=estimated_land_date,
    )
    etl = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = etl.load()
    assert (0, 1) == (updated, created)

    mi_investment_project = MIInvestmentProject.objects.values(*etl.COLUMNS).first()
    assert mi_investment_project['actual_land_date'] == actual_land_date
    assert mi_investment_project['estimated_land_date'] == estimated_land_date
    assert mi_investment_project['land_date'] == expected_land_date


@pytest.mark.parametrize(
    'sector_cluster_id,expected',
    (
        (
            SectorCluster.defence_and_security.value.id,
            SectorCluster.defence_and_security.value.name,
        ),
        (
            SectorCluster.financial_and_professional_services.value.id,
            SectorCluster.financial_and_professional_services.value.name,
        ),
        (None, NO_SECTOR_CLUSTER_ASSIGNED),
    ),
)
def test_sector_cluster(sector_cluster_id, expected):
    """Tests that sector cluster has correct default value."""
    parent_sector = SectorFactory(
        segment='Cats',
        sector_cluster_id=sector_cluster_id,
    )
    sector = SectorFactory(segment='Rockets', parent=parent_sector)
    InvestmentProjectFactory(
        sector_id=sector.id,
    )

    etl = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = etl.load()
    assert (0, 1) == (updated, created)

    mi_investment_project = MIInvestmentProject.objects.values(*etl.COLUMNS).first()
    assert mi_investment_project['sector_cluster'] == expected


@pytest.mark.parametrize(
    'sector_id,expected',
    (
        (
            Sector.renewable_energy_wind.value.id,
            Sector.renewable_energy_wind.value.name,
        ),
        (None, NO_SECTOR_ASSIGNED),
    ),
)
def test_top_level_sector(sector_id, expected):
    """Tests that top level sector has correct default value."""
    InvestmentProjectFactory(
        sector_id=sector_id,
    )

    etl = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = etl.load()
    assert (0, 1) == (updated, created)

    mi_investment_project = MIInvestmentProject.objects.values(*etl.COLUMNS).first()

    assert mi_investment_project['sector_name'] == expected
    assert mi_investment_project['top_level_sector_name'] == expected.split(' :', maxsplit=1)[0]


@pytest.mark.parametrize(
    'uk_region_id,expected',
    (
        (
            UKRegion.west_midlands.value.id,
            UKRegion.west_midlands.value.name,
        ),
        (None, NO_UK_REGION_ASSIGNED),
    ),
)
def test_possible_uk_region_names(uk_region_id, expected):
    """Tests that the field possible uk region names has correct default value."""
    investment_project = InvestmentProjectFactory()
    if uk_region_id:
        investment_project.uk_region_locations.add(parse_uuid(uk_region_id))

    etl = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = etl.load()
    assert (0, 1) == (updated, created)

    mi_investment_project = MIInvestmentProject.objects.values(*etl.COLUMNS).first()

    assert mi_investment_project['possible_uk_region_names'] == expected


@pytest.mark.parametrize(
    'uk_region_id,expected',
    (
        (
            UKRegion.west_midlands.value.id,
            UKRegion.west_midlands.value.name,
        ),
        (None, NO_UK_REGION_ASSIGNED),
    ),
)
def test_actual_uk_region_names(uk_region_id, expected):
    """Tests that the field actual uk region names has correct default value."""
    investment_project = InvestmentProjectFactory()
    if uk_region_id:
        investment_project.actual_uk_regions.add(parse_uuid(uk_region_id))

    etl = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = etl.load()
    assert (0, 1) == (updated, created)

    mi_investment_project = MIInvestmentProject.objects.values(*etl.COLUMNS).first()

    assert mi_investment_project['actual_uk_region_names'] == expected


@pytest.mark.parametrize(
    'actual_uk_region_id,possible_uk_region_id,expected',
    (
        (
            UKRegion.west_midlands.value.id,
            None,
            UKRegion.west_midlands.value.name,
        ),
        (
            None,
            UKRegion.west_midlands.value.id,
            UKRegion.west_midlands.value.name,
        ),
        (
            UKRegion.channel_islands.value.id,
            UKRegion.west_midlands.value.id,
            UKRegion.channel_islands.value.name,
        ),
        (None, None, NO_UK_REGION_ASSIGNED),
    ),
)
def test_uk_region_name(actual_uk_region_id, possible_uk_region_id, expected):
    """Tests that the field uk region name has correct default value."""
    investment_project = InvestmentProjectFactory()
    if actual_uk_region_id:
        investment_project.actual_uk_regions.add(parse_uuid(actual_uk_region_id))
    if possible_uk_region_id:
        investment_project.uk_region_locations.add(parse_uuid(possible_uk_region_id))

    etl = ETLInvestmentProjects(destination=MIInvestmentProject)

    updated, created = etl.load()
    assert (0, 1) == (updated, created)

    mi_investment_project = MIInvestmentProject.objects.values(*etl.COLUMNS).first()
    assert mi_investment_project['uk_region_name'] == expected
