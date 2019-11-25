from uuid import uuid4

import pytest
from django.core.management import call_command

from datahub.company.models import Company
from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.dbmaintenance.management.commands.get_dnb_one_list_tier_companies import (
    _get_company_ids,
)

# TODO: Remove these tests when we are done with the query command

pytestmark = pytest.mark.django_db

ONE_LIST_TIER_A_IDS = [
    'b91bf800-8d53-e311-aef3-441ea13961e2',
    '7e0c261a-d447-e411-985c-e4115bead28a',
]
ONE_LIST_TIER_B_IDS = [
    'bb1bf800-8d53-e311-aef3-441ea13961e2',
    '23ef2218-37f7-4abf-aacb-7c49f65ee1e3',
]
MANAGER_1_ID = uuid4()
MANAGER_2_ID = uuid4()


@pytest.fixture
def one_list_companies():
    """
    Test fixture of sample one list tier companies.
    """
    manager_1 = AdviserFactory(
        first_name='Manager 1',
        pk=MANAGER_1_ID,
    )
    manager_2 = AdviserFactory(
        first_name='Manager 2',
        pk=MANAGER_2_ID,
    )

    tier_a_headquarters = CompanyFactory(
        name='Tier A Headquarters',
        one_list_tier_id=ONE_LIST_TIER_A_IDS[0],
        one_list_account_owner=manager_1,
        duns_number='123456789',
    )
    CompanyFactory(
        name='Tier A Subsidiary No Duns',
        global_headquarters=tier_a_headquarters,
    )
    CompanyFactory(
        name='Tier A Subsidiary With Duns',
        global_headquarters=tier_a_headquarters,
        duns_number='223456789',
    )
    CompanyFactory(
        name='Tier A Standalone',
        one_list_tier_id=ONE_LIST_TIER_A_IDS[1],
        one_list_account_owner=manager_1,
        duns_number='323456789',
    )
    CompanyFactory(
        name='Tier A Standalone Manager 2',
        one_list_tier_id=ONE_LIST_TIER_A_IDS[1],
        one_list_account_owner=manager_2,
        duns_number='423456789',
    )

    tier_b_headquarters = CompanyFactory(
        name='Tier B Headquarters',
        one_list_tier_id=ONE_LIST_TIER_B_IDS[0],
        one_list_account_owner=manager_2,
        duns_number='523456789',
    )
    CompanyFactory(
        name='Tier B Subsidiary No Duns',
        global_headquarters=tier_b_headquarters,
    )
    CompanyFactory(
        name='Tier B Subsidiary With Duns',
        global_headquarters=tier_b_headquarters,
        duns_number='623456789',
    )
    CompanyFactory(
        name='Tier B Standalone',
        one_list_tier_id=ONE_LIST_TIER_B_IDS[1],
        one_list_account_owner=manager_2,
        duns_number='723456789',
    )
    CompanyFactory(
        name='Tier B Standalone Manager 1',
        one_list_tier_id=ONE_LIST_TIER_B_IDS[1],
        one_list_account_owner=manager_1,
        duns_number='823456789',
    )

    CompanyFactory(
        name='No Tier',
        duns_number='923456789',
    )


@pytest.mark.parametrize(
    'one_list_tier_ids,account_manager_ids,expected_company_names',
    (
        # Test filtering by one tier, one manager
        (
            ONE_LIST_TIER_A_IDS,
            [MANAGER_1_ID],
            {'Tier A Headquarters', 'Tier A Subsidiary With Duns', 'Tier A Standalone'},
        ),
        # Test filtering by one tier, two managers
        (
            ONE_LIST_TIER_A_IDS,
            [MANAGER_1_ID, MANAGER_2_ID],
            {
                'Tier A Headquarters',
                'Tier A Subsidiary With Duns',
                'Tier A Standalone',
                'Tier A Standalone Manager 2',
            },
        ),
        # Test filtering by one tier, no managers
        (
            ONE_LIST_TIER_A_IDS,
            [],
            {
                'Tier A Headquarters',
                'Tier A Subsidiary With Duns',
                'Tier A Standalone',
                'Tier A Standalone Manager 2',
            },
        ),
        # Test filtering by two tiers, no managers
        (
            ONE_LIST_TIER_A_IDS + ONE_LIST_TIER_B_IDS,
            [],
            {
                'Tier A Headquarters',
                'Tier A Subsidiary With Duns',
                'Tier A Standalone',
                'Tier A Standalone Manager 2',
                'Tier B Headquarters',
                'Tier B Subsidiary With Duns',
                'Tier B Standalone',
                'Tier B Standalone Manager 1',
            },
        ),
    ),
)
def test_get_company_ids(
    one_list_companies,
    one_list_tier_ids,
    account_manager_ids,
    expected_company_names,
):
    """
    Test the _get_company_ids helper function.
    """
    company_ids = _get_company_ids(one_list_tier_ids, account_manager_ids)
    companies = Company.objects.filter(pk__in=company_ids)
    company_names = {company.name for company in companies}
    assert company_names == set(expected_company_names)


def test_command(caplog, one_list_companies):
    """
    Test the command prints out ids for the correct companies.
    """
    caplog.set_level('INFO')

    call_command(
        'get_dnb_one_list_tier_companies',
        one_list_tier_ids=ONE_LIST_TIER_A_IDS,
        account_manager_ids=[MANAGER_1_ID],
    )

    expected_company_names = [
        'Tier A Headquarters',
        'Tier A Subsidiary With Duns',
        'Tier A Standalone',
    ]
    expected_companies = Company.objects.filter(name__in=expected_company_names).values_list('id')
    expected_company_ids = [str(result[0]) for result in expected_companies]

    for expected_id in expected_company_ids:
        assert expected_id in caplog.text
