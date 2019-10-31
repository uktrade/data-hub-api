import pytest
from dateutil.parser import parse as dateutil_parse
from django.conf import settings
from django.db.models import CharField, DateField, Value
from django.db.models.functions import Coalesce

from datahub.company.test.factories import CompanyFactory
from datahub.core.constants import SectorCluster
from datahub.core.query_utils import (
    get_choices_as_case_expression,
)
from datahub.investment.project.constants import Involvement
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.metadata.test.factories import SectorFactory
from datahub.mi_dashboard.constants import NO_SECTOR_CLUSTER_ASSIGNED
from datahub.mi_dashboard.query_utils import (
    get_collapse_status_name_expression,
    get_country_url,
    get_financial_year_from_land_date_expression,
    get_level_of_involvement_simplified_expression,
    get_other_field_if_null_or_empty_expression,
    get_sector_cluster_expression,
)

pytestmark = pytest.mark.django_db

my_project_sector_to_sector_cluster = {
    'Cats in space': 'Catering',
    'Cats on water': 'Catering',
    'Parrots on trees': 'Parroting',
}

my_countries_to_region = {
    'Cats in space': 'Nebula',
}


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
def test_get_sector_cluster_from_project_sector(sector_cluster_id, expected):
    """Tests that sector cluster can be mapped from sector."""
    parent_sector = SectorFactory(
        segment='Cats',
        sector_cluster_id=sector_cluster_id,
    )
    sector = SectorFactory(segment='Rockets', parent=parent_sector)
    InvestmentProjectFactory(
        sector_id=sector.id,
    )
    query = InvestmentProject.objects.annotate(
        sector_name=get_sector_name_subquery('sector'),
        sector_cluster=get_sector_cluster_expression('sector'),
    ).values('sector_cluster')

    for project in query.all():
        assert project['sector_cluster'] == expected


@pytest.mark.parametrize(
    'involvement,expected',
    (
        (Involvement.hq_only.value.id, 'involved'),
        (Involvement.no_involvement.value.id, 'not_involved'),
        (None, 'unspecified'),
    ),
)
def test_get_level_of_involvement_simplified_expression(involvement, expected):
    """Tests that simplified level of involvement can be queried."""
    InvestmentProjectFactory(
        level_of_involvement_id=involvement,
    )
    query = InvestmentProject.objects.annotate(
        level_of_involvement_simplified=get_level_of_involvement_simplified_expression(),
    ).values('level_of_involvement_simplified')

    investment_project = query.first()
    assert investment_project['level_of_involvement_simplified'] == expected


@pytest.mark.parametrize(
    'status,expected',
    (
        ('Ongoing', 'Ongoing / Won'),
        ('Won', 'Ongoing / Won'),
        ('Completed', 'Completed'),
    ),
)
def test_get_collapse_project_status_expression(status, expected):
    """Tests if Ongoing and Won status get the same value."""
    InvestmentProjectFactory(
        status=status,
    )
    query = InvestmentProject.objects.annotate(
        status_name=get_choices_as_case_expression(InvestmentProject, 'status'),
        project_status=get_collapse_status_name_expression(),
    ).values('project_status')

    investment_project = query.first()
    assert investment_project['project_status'] == expected


@pytest.mark.parametrize(
    'value_a,value_b,expected',
    (
        ('cat', 'lion', 'cat'),
        (None, 'lion', 'lion'),
        ('', 'lion', 'lion'),
    ),
)
def test_get_other_field_if_null_or_empty_expression(value_a, value_b, expected):
    """Tests if other field can be fetched if field has empty value or is None."""
    InvestmentProjectFactory()
    query = InvestmentProject.objects.annotate(
        possibly_null_value=Value(value_a, output_field=CharField(null=True)),
        always_value=Value(value_b, output_field=CharField()),
        some_property=get_other_field_if_null_or_empty_expression(
            'possibly_null_value',
            'always_value',
        ),
    ).values('some_property')

    investment_project = query.first()
    assert investment_project['some_property'] == expected


@pytest.mark.parametrize(
    'value_a,value_b,expected',
    (
        ('2015-05-30', '2011-01-31', '2015-05-30'),
        (None, '2011-01-31', '2011-01-31'),
    ),
)
def test_get_other_date_if_null_expression(value_a, value_b, expected):
    """Tests if other field can be fetched if field has empty value or is None."""
    InvestmentProjectFactory()
    query = InvestmentProject.objects.annotate(
        possibly_null_value=Value(value_a, output_field=DateField(null=True)),
        always_value=Value(value_b, output_field=DateField()),
        some_property=Coalesce(
            'possibly_null_value',
            'always_value',
        ),
    ).values('some_property')

    investment_project = query.first()
    assert investment_project['some_property'] == dateutil_parse(expected).date()


@pytest.mark.parametrize(
    'land_date,expected',
    (
        ('2015-05-30', '2015/2016'),
        ('2015-02-10', '2014/2015'),
        ('2018-04-06', '2018/2019'),
        ('2018-04-01', '2018/2019'),
        ('2017-03-31', '2016/2017'),
        ('2017-01-01', '2016/2017'),
        (None, ''),
    ),
)
def test_get_financial_year_from_land_date(land_date, expected):
    """Test that expression gets a financial year."""
    InvestmentProjectFactory(
        actual_land_date=land_date,
        estimated_land_date=None,
    )
    query = InvestmentProject.objects.annotate(
        land_date=Coalesce(
            'actual_land_date',
            'estimated_land_date',
        ),
        financial_year=get_financial_year_from_land_date_expression(),
    ).values('financial_year')

    investment_project = query.first()
    assert investment_project['financial_year'] == expected


def test_get_country_url():
    """Test that expression gets a country url."""
    investment_project = InvestmentProjectFactory(
        investor_company=CompanyFactory(),
    )

    query = InvestmentProject.objects.annotate(
        country_url=get_country_url(),
    ).values('country_url')

    result = query.first()

    url_prefix = settings.DATAHUB_FRONTEND_URL_PREFIXES['mi_fdi_dashboard_country']
    url = f'{url_prefix}{investment_project.investor_company.address_country_id}'
    assert result['country_url'] == url
