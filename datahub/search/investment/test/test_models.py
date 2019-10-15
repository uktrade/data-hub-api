import datetime
from decimal import Decimal
from unittest import mock

import pytest

from datahub.core import constants
from datahub.investment.project.constants import Involvement
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import (
    AdviserFactory,
    CompanyFactory,
    GVAMultiplierFactory,
    InvestmentProjectFactory,
)
from datahub.search.investment.models import InvestmentProject as ESInvestmentProject

pytestmark = pytest.mark.django_db


@pytest.fixture
def project_with_max_gross_value_added():
    """Test fixture returns an investment project with the max gross value."""
    gva_multiplier = GVAMultiplierFactory(
        multiplier=Decimal('9.999999'),
        financial_year=1980,
    )

    with mock.patch(
        'datahub.investment.project.gva_utils.GrossValueAddedCalculator._get_gva_multiplier',
    ) as mock_get_multiplier:
        mock_get_multiplier.return_value = gva_multiplier
        yield InvestmentProjectFactory(
            investment_type_id=constants.InvestmentType.fdi.value.id,
            name='won project',
            description='investmentproject3',
            estimated_land_date=datetime.date(2027, 9, 13),
            actual_land_date=datetime.date(2022, 11, 13),
            investor_company=CompanyFactory(
                address_country_id=constants.Country.united_kingdom.value.id,
            ),
            project_manager=AdviserFactory(),
            project_assurance_adviser=AdviserFactory(),
            fdi_value_id=constants.FDIValue.higher.value.id,
            status=InvestmentProject.STATUSES.won,
            uk_region_locations=[
                constants.UKRegion.north_west.value.id,
            ],
            level_of_involvement_id=Involvement.hq_only.value.id,
            likelihood_to_land_id=None,
            foreign_equity_investment=9999999999999999999,
        )


def test_investment_project_to_dict(es_with_signals):
    """Tests conversion of db model to dict."""
    project = InvestmentProjectFactory()
    result = ESInvestmentProject.db_object_to_dict(project)

    keys = {
        'id',
        'allow_blank_estimated_land_date',
        'allow_blank_possible_uk_regions',
        'business_activities',
        'client_contacts',
        'client_relationship_manager',
        'investor_company',
        'investor_company_country',
        'investor_type',
        'level_of_involvement',
        'investment_type',
        'stage',
        'referral_source_activity',
        'referral_source_adviser',
        'sector',
        'project_code',
        'created_on',
        'created_by',
        'modified_on',
        'archived',
        'archived_on',
        'archived_reason',
        'archived_by',
        'name',
        'description',
        'comments',
        'anonymous_description',
        'estimated_land_date',
        'actual_land_date',
        'approved_commitment_to_invest',
        'approved_fdi',
        'approved_good_value',
        'approved_high_value',
        'approved_landed',
        'approved_non_fdi',
        'intermediate_company',
        'referral_source_activity_website',
        'referral_source_activity_marketing',
        'referral_source_activity_event',
        'fdi_type',
        'fdi_value',
        'client_cannot_provide_total_investment',
        'total_investment',
        'client_cannot_provide_foreign_investment',
        'foreign_equity_investment',
        'gross_value_added',
        'government_assistance',
        'some_new_jobs',
        'specific_programme',
        'number_new_jobs',
        'will_new_jobs_last_two_years',
        'average_salary',
        'number_safeguarded_jobs',
        'r_and_d_budget',
        'non_fdi_r_and_d_budget',
        'associated_non_fdi_r_and_d_project',
        'new_tech_to_uk',
        'export_revenue',
        'client_requirements',
        'uk_region_locations',
        'actual_uk_regions',
        'delivery_partners',
        'site_decided',
        'address_1',
        'address_2',
        'address_town',
        'address_postcode',
        'uk_company_decided',
        'uk_company',
        'project_manager',
        'proposal_deadline',
        'project_assurance_adviser',
        'team_members',
        'likelihood_to_land',
        'project_arrived_in_triage_on',
        'quotable_as_public_case_study',
        'other_business_activity',
        'status',
        'reason_delayed',
        'reason_abandoned',
        'date_abandoned',
        'reason_lost',
        'date_lost',
        'country_lost_to',
        'country_investment_originates_from',
        'level_of_involvement_simplified',
    }

    assert set(result.keys()) == keys


def test_investment_project_dbmodels_to_es_documents(es_with_signals):
    """Tests conversion of db models to Elasticsearch documents."""
    projects = InvestmentProjectFactory.create_batch(2)

    result = ESInvestmentProject.db_objects_to_es_documents(projects)

    assert len(list(result)) == len(projects)


def test_max_values_of_doubles_gross_value_added_and_foreign_equity_investment(
    es_with_signals,
    project_with_max_gross_value_added,
):
    """
    Tests the max value of gross value added and foreign equity investment.

    Both gross_value_added and foreign_equity_investment are decimal fields but the elasticsearch
    library casts them to floats so are treated as floats.

    The test highlights a known inaccuracy when dealing with large floating point numbers.

    https://docs.python.org/3.6/tutorial/floatingpoint.html

    This inaccuracy is going to be ignored as although possible this shouldn't happen in
    the real world with the gva multiplier value unlikely to exceed 2.

    """
    foreign_equity_investment_value = 9999999999999999999
    less_accurate_expected_foreign_equity_investment_value = 10000000000000000000

    expected_gross_value_added_value = 99999989999999999991
    less_accurate_expected_gross_value_added = 99999989999999991808

    project = project_with_max_gross_value_added
    assert project.gross_value_added == expected_gross_value_added_value

    result = ESInvestmentProject.db_object_to_dict(project)
    assert result['foreign_equity_investment'] == foreign_equity_investment_value
    assert result['gross_value_added'] == expected_gross_value_added_value

    # Re-fetch the project from elasticsearch and
    # re-check the values against the less accurate values.
    project_in_es = ESInvestmentProject.get(
        id=project.pk,
        index=ESInvestmentProject.get_read_alias(),
    )

    assert (
        project_in_es['foreign_equity_investment']
        == less_accurate_expected_foreign_equity_investment_value
    )
    assert project_in_es['gross_value_added'] == less_accurate_expected_gross_value_added
