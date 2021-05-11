import pytest

from datahub.bed_api.constants import (
    BusinessArea,
    ContactType,
    HighLevelSector,
    JobType,
    LowLevelSector,
    Salutation,
)
from datahub.bed_api.factories import BedFactory
from datahub.bed_api.models import EditAccount, EditContact
from datahub.bed_api.repositories import AccountRepository, ContactRepository
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
    high_level_sector = faker.random_element(
        elements=(
            HighLevelSector.defense,
            HighLevelSector.food_and_agriculture,
            HighLevelSector.energy,
            HighLevelSector.financial_services,
            HighLevelSector.environmental_services,
            HighLevelSector.education_and_research,
            HighLevelSector.creative_industries,
            HighLevelSector.advanced_manufacturing,
        ),
    )
    return high_level_sector


@pytest.fixture
def generate_low_level_sector(faker):
    """
    Generate random low level sector
    :param faker: Faker Library
    :return: Random low level sector value
    """
    low_level_sector = faker.random_element(
        elements=(
            LowLevelSector.consumers,
            LowLevelSector.digital,
            LowLevelSector.digital_infrastructure,
            LowLevelSector.retail,
            LowLevelSector.real_estate,
            LowLevelSector.telecoms,
        ),
    )
    return low_level_sector


@pytest.fixture
def generate_uk_region_name(faker):
    """
    Generate random UK Region name
    :param faker: Faker Library
    :return: Random UK region name value
    """
    uk_region = faker.random_element(
        elements=(
            UKRegion.all.value.name,
            UKRegion.channel_islands.value.name,
            UKRegion.alderney.value.name,
            UKRegion.england.value.name,
            UKRegion.east_midlands.value.name,
            UKRegion.east_of_england.value.name,
            UKRegion.fdi_hub.value.name,
            UKRegion.guernsey.value.name,
            UKRegion.isle_of_man.value.name,
            UKRegion.jersey.value.name,
            UKRegion.london.value.name,
            UKRegion.north_east.value.name,
            UKRegion.north_west.value.name,
            UKRegion.northern_ireland.value.name,
            UKRegion.sark.value.name,
            UKRegion.scotland.value.name,
            UKRegion.south_west.value.name,
            UKRegion.south_east.value.name,
            UKRegion.ukti_dubai_hub.value.name,
            UKRegion.wales.value.name,
            UKRegion.yorkshire_and_the_humber.value.name,
            UKRegion.west_midlands.value.name,
        ),

    )
    return uk_region


@pytest.fixture
def generate_salutation(faker):
    """
    Generate random salutation
    :param faker: Faker Library
    :return: Random salutation value
    """
    salutation = faker.random_element(
        elements=(
            Salutation.mrs,
            Salutation.mr,
            Salutation.prof,
            Salutation.dame,
            Salutation.dr,
            Salutation.lord,
            Salutation.miss,
            Salutation.ms,
            Salutation.sir,
            Salutation.right_honourable,
        ),
    )
    return salutation


@pytest.fixture
def generate_country_names(faker):
    """
    Generate random country names array
    :param faker: Faker Library
    :return: Random country names sector value
    """
    countries = faker.random_elements(
        elements=(
            Country.united_states.value.name,
            Country.united_kingdom.value.name,
            # CHECK: ('INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST',
            #   'fields': ['Global_Office_Locations__c']}]
            # Country.isle_of_man.value.name,
            Country.canada.value.name,
            Country.france.value.name,
            Country.greece.value.name,
            Country.ireland.value.name,
            Country.italy.value.name,
        ),
        unique=True,
    )
    # TODO: Create full list to see issues with mappings like the one above
    return countries


@pytest.fixture
def generate_job_type(faker):
    """
    Generate random job type
    :param faker: Faker Library
    :return: Random JobType value
    """
    job_type = faker.random_element(
        elements=(
            JobType.consultant,
            JobType.hr,
            JobType.ceo,
            JobType.chairperson,
            JobType.communications,
            JobType.corporate_social_responsibility,
            JobType.director,
            JobType.education,
            JobType.engineering,
            JobType.executive,
            JobType.finance,
            JobType.financial_director,
            JobType.founder,
            JobType.head_of_public_affairs,
            JobType.health_professional,
            JobType.head_of_public_affairs,
            JobType.hr,
            JobType.legal,
            JobType.manager,
            JobType.operations,
            JobType.other,
            JobType.owner,
            JobType.policy,
            JobType.president,
            JobType.public_affairs,
        ),
    )
    return job_type


@pytest.fixture
def generate_business_area(faker):
    """
    Generate random business area
    :param faker: Faker Library
    :return: Random BusinessArea value
    """
    business_area = faker.random_element(
        elements=(
            BusinessArea.advanced_manufacturing,
            BusinessArea.civil_society,
            BusinessArea.consumer_and_retail,
            BusinessArea.creative_industries,
            BusinessArea.defense,
            BusinessArea.education_and_research,
            BusinessArea.energy,
            BusinessArea.environmental_services,
            BusinessArea.financial_services,
            BusinessArea.food_and_agriculture,
            BusinessArea.professional,
        ),
    )
    return business_area


@pytest.fixture
def generate_account(
    faker,
    generate_high_level_sector,
    generate_low_level_sector,
    generate_uk_region_name,
    generate_country_names,
):
    """
    Generate account with random data
    :param faker:
    :param generate_high_level_sector:
    :param generate_low_level_sector:
    :param generate_uk_region_name:
    :param generate_country_names:
    :return: New EditAccount with random values
    """
    new_account = EditAccount(
        name=faker.company(),
        high_level_sector=generate_high_level_sector,
        low_level_sector=generate_low_level_sector,
    )
    new_account.BillingStreet = faker.street_address()
    new_account.BillingCity = faker.city()
    new_account.BillingState = faker.street_name()
    new_account.BillingPostalCode = faker.postcode()
    new_account.BillingCountry = faker.country()
    new_account.ShippingStreet = faker.street_name()
    new_account.ShippingCity = faker.city()
    new_account.ShippingState = faker.street_name()
    new_account.ShippingPostalCode = faker.postcode()
    new_account.ShippingCountry = faker.country()
    new_account.UK_Region__c = generate_uk_region_name
    new_account.Global_Office_Locations__c = ';'.join(generate_country_names)
    new_account.Country_HQ__c = faker.random_element(elements=generate_country_names)
    return new_account


@pytest.fixture
def generate_contact(
    faker,
    generate_salutation,
    generate_job_type,
    generate_business_area,
):
    """
    Generate new EditContact with random values
    :param faker:
    :param generate_salutation:
    :param generate_job_type:
    :param generate_business_area:
    :return: New EditContact with random fake data
    """
    firstname = faker.first_name()
    lastname = faker.last_name()
    email = f'{firstname.lower()}.{lastname.lower()}@digital.trade.gov.uk'
    contact = EditContact(
        salutation=generate_salutation,
        first_name=firstname,
        last_name=lastname,
        email=email,
        account_id='0010C00000HGsfFBJH',
    )
    contact.Suffix = faker.suffix()
    contact.MiddleName = faker.first_name()
    contact.Phone = faker.phone_number()
    contact.MobilePhone = faker.phone_number()
    contact.Notes__c = faker.text(max_nb_chars=100)
    contact.Contact_Type__c = ContactType.external
    contact.Job_Title__c = faker.job()
    contact.Job_Type__c = generate_job_type
    contact.Business_Area__c = generate_business_area
    return contact
