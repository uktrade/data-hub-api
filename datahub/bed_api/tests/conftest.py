import uuid

import pytest

from datahub.bed_api.constants import (
    HighLevelSector,
    LowLevelSector,
)
from datahub.bed_api.entities import (
    Account,
)
from datahub.bed_api.factories import BedFactory
from datahub.bed_api.repositories import (
    AccountRepository,
)
from datahub.core.constants import Country, UKRegion


@pytest.fixture
def salesforce():
    """Create salesforce instance using the BedFactory"""
    bed_factory = BedFactory()
    salesforce = bed_factory.create()
    return salesforce


@pytest.fixture
def account_repository(salesforce):
    """
    Creates instance of account repository

    :param salesforce: BedFactory creating an instance of salesforce

    :return: Instance of AccountRepository
    """
    repository = AccountRepository(salesforce)
    return repository


@pytest.fixture
def high_level_sector(faker):
    """
    Generate random high level sector

    :param faker: Faker Library

    :return: Random high level sector value
    """
    return get_random_element(
        faker,
        HighLevelSector.values(HighLevelSector),
    )


@pytest.fixture
def low_level_sector(faker):
    """
    Generate random low level sector

    :param faker: Faker Library

    :return: Random low level sector value
    """
    return get_random_element(
        faker,
        LowLevelSector.values(LowLevelSector),
    )


@pytest.fixture
def uk_region_name(faker):
    """
    Generate random UK Region name

    :param faker: Faker Library

    :return: Random UK region name value
    """
    return get_random_element(
        faker,
        (
            # CHECK Commented out in the end including others
            # UKRegion.all.value.name,
            # UKRegion.channel_islands.value.name,
            UKRegion.alderney.value.name,
            UKRegion.england.value.name,
            UKRegion.east_midlands.value.name,
            UKRegion.east_of_england.value.name,
            # UKRegion.fdi_hub.value.name,
            UKRegion.guernsey.value.name,
            UKRegion.isle_of_man.value.name,
            UKRegion.jersey.value.name,
            UKRegion.london.value.name,
            UKRegion.north_east.value.name,
            UKRegion.north_west.value.name,
            UKRegion.northern_ireland.value.name,
            # UKRegion.sark.value.name,
            UKRegion.scotland.value.name,
            UKRegion.south_west.value.name,
            UKRegion.south_east.value.name,
            # UKRegion.ukti_dubai_hub.value.name,
            UKRegion.wales.value.name,
            UKRegion.yorkshire_and_the_humber.value.name,
            UKRegion.west_midlands.value.name,
        ),
    )


@pytest.fixture
def country_names(faker):
    """
    Generate random country names array

    :param faker: Faker Library

    :return: Random country names value
    """
    return get_random_elements(
        faker,
        (
            Country.argentina.value.name,
            Country.azerbaijan.value.name,
            Country.cayman_islands.value.name,
            Country.japan.value.name,
            Country.canada.value.name,
            Country.france.value.name,
            Country.greece.value.name,
            Country.ireland.value.name,
            Country.italy.value.name,
            Country.united_states.value.name,
            Country.united_kingdom.value.name,
        ),
    )


@pytest.fixture
def company_number(faker):
    """
    Generate random company number

    :param faker: Faker Library

    :return: Random company value
    """
    return get_random_element(
        faker,
        (
            str(uuid.uuid4()),
            str(uuid.uuid4()),
        ),
    )


@pytest.fixture
def account(
    faker,
    high_level_sector,
    low_level_sector,
    uk_region_name,
    country_names,
    company_number,
):
    """
    Generate account with random data

    :param faker: Faker Library
    :param high_level_sector: sector mapping
    :param low_level_sector: sector mapping
    :param uk_region_name: uk regions
    :param country_names: country names
    :param company_number: company numbers

    :return: New Account with random values
    """
    new_account = Account(
        datahub_id=str(uuid.uuid4()),
        name=faker.company(),
        high_level_sector=high_level_sector,
        low_level_sector=low_level_sector,
    )
    new_account.billing_street = faker.street_address()
    new_account.billing_city = faker.city()
    new_account.billing_state = faker.street_name()
    new_account.billing_postal_code = faker.postcode()
    new_account.billing_country = faker.country()
    new_account.shipping_street = faker.street_name()
    new_account.shipping_city = faker.city()
    new_account.shipping_state = faker.street_name()
    new_account.shipping_postal_code = faker.postcode()
    new_account.shipping_country = faker.country()
    new_account.uk_region = uk_region_name
    new_account.country_hq = faker.random_element(elements=country_names)
    new_account.company_number = company_number
    new_account.companies_house_id = company_number
    new_account.company_website = faker.url()

    return new_account


def get_random_element(faker, elements):
    """
    Get random element from faker using elements list

    :param faker: Faker Library
    :param elements: List of elements

    :return: Single element of the list
    """
    return faker.random_element(elements=elements)


def get_random_elements(faker, elements):
    """
    Generate random unique sorted elements using elements

    :param faker: Faker Library
    :param elements: List of elements

    :return: Random unique elements value sorted
    """
    result = faker.random_elements(
        elements=elements,
        unique=True,
    )
    return sorted(result)
