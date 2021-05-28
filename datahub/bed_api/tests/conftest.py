import uuid

import pytest

from datahub.bed_api.constants import (
    BusinessArea,
    ContactType,
    HighLevelSector,
    JobType,
    LowLevelSector,
    PolicyArea,
    Salutation,
    SectorsAffected,
)
from datahub.bed_api.entities import (
    Account,
    Contact,
)
from datahub.bed_api.factories import BedFactory
from datahub.bed_api.repositories import (
    AccountRepository,
    ContactRepository,
)
from datahub.core.constants import Country, UKRegion


@pytest.fixture
def salesforce():
    """Create salesforce instance using the BedFactory"""
    bed_factory = BedFactory()
    salesforce = bed_factory.create()
    return salesforce


@pytest.fixture
def contact_repository(salesforce):
    """
    Creates instance of contact repository

    :param salesforce: BedFactory creating an instance of salesforce

    :return: Instance of ContactRepository
    """
    repository = ContactRepository(salesforce)
    return repository


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
def generate_high_level_sector(faker):
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
def generate_low_level_sector(faker):
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
def generate_uk_region_name(faker):
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
def generate_salutation(faker):
    """
    Generate random salutation

    :param faker: Faker Library

    :return: Random salutation value
    """
    return get_random_element(
        faker,
        Salutation.values(Salutation),
    )


@pytest.fixture
def generate_country_names(faker):
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
def generate_job_type(faker):
    """
    Generate random job type

    :param faker: Faker Library

    :return: Random JobType value
    """
    return get_random_element(
        faker,
        JobType.values(JobType),
    )


@pytest.fixture
def generate_business_area(faker):
    """
    Generate random business area

    :param faker: Faker Library

    :return: Random BusinessArea value
    """
    return get_random_element(
        faker,
        BusinessArea.values(BusinessArea),
    )


@pytest.fixture
def generate_company_number(faker):
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
def generate_policy_areas(faker):
    """
    Generate random policy_area arrays

    :param faker: Faker Library

    :return: Random policy areas array
    """
    return get_random_elements(
        faker,
        PolicyArea.values(PolicyArea),
    )


@pytest.fixture
def generate_sectors_affected(faker):
    """
    Generate random SectorsAffected array

    :param faker: Faker Library

    :return: Random SectorsAffected array
    """
    return get_random_elements(
        faker,
        SectorsAffected.values(SectorsAffected),
    )


@pytest.fixture
def generate_account(
    faker,
    generate_high_level_sector,
    generate_low_level_sector,
    generate_uk_region_name,
    generate_country_names,
    generate_company_number,
):
    """
    Generate account with random data

    :param faker: Faker Library
    :param generate_high_level_sector: sector mapping
    :param generate_low_level_sector: sector mapping
    :param generate_uk_region_name: uk regions
    :param generate_country_names: country names
    :param generate_company_number: company numbers

    :return: New Account with random values
    """
    new_account = Account(
        datahub_id=str(uuid.uuid4()),
        name=faker.company(),
        high_level_sector=generate_high_level_sector,
        low_level_sector=generate_low_level_sector,
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
    new_account.uk_region = generate_uk_region_name
    new_account.country_hq = get_random_element(faker, generate_country_names)
    new_account.company_number = generate_company_number
    new_account.companies_house_id = generate_company_number
    new_account.company_website = faker.url()

    return new_account


@pytest.fixture
def generate_contact(
    faker,
    generate_salutation,
    generate_job_type,
    generate_business_area,
):
    """
    Generate new Contact with random values

    :param faker: Faker Library
    :param generate_salutation:
    :param generate_job_type:
    :param generate_business_area:

    :return: New Contact with random fake data
    """
    firstname = faker.first_name()
    lastname = faker.last_name()
    email = f'{firstname.lower()}.{lastname.lower()}@digital.trade.gov.uk'
    contact = Contact(
        datahub_id=str(uuid.uuid4()),
        first_name=firstname,
        last_name=lastname,
        email=email,
        account_id=str(uuid.uuid4()),
    )
    contact.salutation = generate_salutation
    contact.suffix = faker.suffix()
    contact.middle_name = faker.first_name()
    contact.phone = faker.phone_number()
    contact.mobile_phone = faker.phone_number()
    contact.notes = faker.text(max_nb_chars=100)
    contact.contact_type = ContactType.external
    contact.job_title = faker.job()
    contact.job_type = generate_job_type
    contact.business_area = generate_business_area
    contact.assistant_name = faker.name()
    contact.assistant_email = faker.company_email()
    contact.assistant_phone = faker.phone_number()
    return contact


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
