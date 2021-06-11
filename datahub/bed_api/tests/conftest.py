import datetime
import uuid

import pytest

from datahub.bed_api.constants import (
    BusinessArea,
    Classification,
    ContactType,
    DepartmentEyes,
    HighLevelSector,
    InteractionType,
    IssueType,
    JobType,
    LowLevelSector,
    PolicyArea,
    Salutation,
    SectorsAffected,
    Sentiment,
    TopIssuesByRank,
    TransparencyStatus,
)
from datahub.bed_api.entities import (
    Account,
    Contact,
    Event,
    EventAttendee,
    PolicyIssues,
)
from datahub.bed_api.factories import BedFactory
from datahub.bed_api.repositories import (
    AccountRepository,
    ContactRepository,
    EventAttendeeRepository,
    EventRepository,
    PolicyIssuesRepository,
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
    return ContactRepository(salesforce)


@pytest.fixture
def account_repository(salesforce):
    """
    Creates instance of account repository

    :param salesforce: BedFactory creating an instance of salesforce

    :return: Instance of AccountRepository
    """
    return AccountRepository(salesforce)


@pytest.fixture
def event_repository(salesforce):
    """
    Creates instance of event repository

    :param salesforce: BedFactory creating an instance of salesforce

    :return: Instance of EventRepository
    """
    return EventRepository(salesforce)


@pytest.fixture
def event_attendee_repository(salesforce):
    """
    Creates instance of event repository

    :param salesforce: BedFactory creating an instance of salesforce

    :return: Instance of EventAttendeeRepository
    """
    return EventAttendeeRepository(salesforce)


@pytest.fixture
def policy_issues_repository(salesforce):
    """
    Creates instance of policy issues repository

    :param salesforce: BedFactory creating an instance of salesforce

    :return: Instance of PolicyIssuesRepository
    """
    return PolicyIssuesRepository(salesforce)


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
def salutation(faker):
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
def issue_types(faker):
    """
    Generate random issue types array

    :param faker: Faker Library

    :return: Random issue topics value
    """
    return get_random_elements(
        faker,
        IssueType.values(IssueType),
    )


@pytest.fixture
def issue_type(faker):
    """
    Generate random issue type

    :param faker: Faker Library

    :return: Random issue type
    """
    return get_random_element(
        faker,
        IssueType.values(IssueType),
    )


@pytest.fixture
def job_type(faker):
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
def business_area(faker):
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
def interaction_type(faker):
    """
    Generate random interaction type

    :param faker: Faker Library

    :return: Random interaction type
    """
    return get_random_element(
        faker,
        InteractionType.values(InteractionType),
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
def transparency_status(faker):
    """
    Generate random transparency status

    :param faker: Faker Library

    :return: Random transparency status
    """
    return get_random_element(
        faker,
        TransparencyStatus.values(TransparencyStatus),
    )


@pytest.fixture
def sentiment(faker):
    """
    Generate sentiment

    :param faker: Faker Library

    :return: Random sentiment
    """
    return get_random_element(
        faker,
        Sentiment.values(Sentiment),
    )


@pytest.fixture
def department_eyes(faker):
    """
    Generate random department eyes

    :param faker: Faker Library

    :return: Random transparency status
    """
    return get_random_element(
        faker,
        DepartmentEyes.values(DepartmentEyes),
    )


@pytest.fixture
def policy_areas(faker):
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
def classification(faker):
    """
    Generate random Classification

    :param faker: Faker Library

    :return: Random Classification
    """
    return get_random_element(
        faker,
        Classification.values(Classification),
    )


@pytest.fixture
def sectors_affected(faker):
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


@pytest.fixture
def contact(
    faker,
    salutation,
    job_type,
    business_area,
):
    """
    Generate new Contact with random values

    :param faker: Faker Library
    :param salutation: Random Salutation
    :param job_type: Random JobType
    :param business_area: Random BusinessArea

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
    contact.salutation = salutation
    contact.suffix = faker.suffix()
    contact.middle_name = faker.first_name()
    contact.phone = faker.phone_number()
    contact.mobile_phone = faker.phone_number()
    contact.notes = faker.text(max_nb_chars=100)
    contact.contact_type = ContactType.external
    contact.job_title = faker.job()
    contact.job_type = job_type
    contact.business_area = business_area
    contact.assistant_name = faker.name()
    contact.assistant_email = faker.company_email()
    contact.assistant_phone = faker.phone_number()
    return contact


@pytest.fixture
def event(
    faker,
    interaction_type,
    uk_region_name,
    transparency_status,
    issue_types,
    department_eyes,
):
    """
    Generate new Event with random values

    :param faker: Faker Library
    :param interaction_type: Random generate InteractionType
    :param uk_region_name: Random uk region
    :param transparency_status: Random transparency status
    :param issue_types: Random issue topics array
    :param department_eyes: Random department eyes only value

    :return: New Event with random fake data
    """
    event = Event(
        name=f'Event Integration Test {datetime.datetime.today()}',
        datahub_id=str(uuid.uuid4()),
        title=f'Title on {datetime.datetime.today()}',
    )
    event.event_date = faker.date()
    event.description = faker.text()
    event.interaction_type = interaction_type
    event.webinar_information = faker.text()
    event.address = faker.address()
    event.location = faker.street_address()
    event.city_town = faker.city()
    event.region = uk_region_name
    event.country = faker.country()
    event.attendees = faker.text()
    event.contacts_to_share = faker.text()
    event.transparency_reason_for_meeting = faker.text()
    event.transparency_status = transparency_status
    event.issue_topics = ';'.join(issue_types)
    event.hmg_lead_email = faker.company_email()
    event.department_eyes_only = department_eyes
    return event


@pytest.fixture
def event_attendee(
    faker,
):
    """
    Generate new Event Attendee test data

    :param faker: Faker data generator
    """
    event_attendee = EventAttendee(
        datahub_id=str(uuid.uuid4()),
        event_id=str(uuid.uuid4()),
        contact_id=str(uuid.uuid4()),
    )
    event_attendee.name = f'Event Attendee Integration Test {datetime.datetime.today()}'
    event_attendee.email = faker.company_email()
    return event_attendee


@pytest.fixture
def policy_issues(
    faker,
    issue_type,
    uk_region_name,
    policy_areas,
    sentiment,
    classification,
    sectors_affected,
    country_names,
):
    """
    Generate new Event Attendee test data

    :param faker: Faker data generator
    :param issue_type: Data generated for issue type
    :param uk_region_name: Data generated for uk regions
    :param policy_areas: Data generated for policy areas
    :param sentiment: Data generated for sentiment
    :param classification: Data generated for classification
    :param sectors_affected: Data generated for sectors effected
    :param country_names: Data generated for Country names
    """
    policy_areas = ';'.join(policy_areas)
    sectors_effected = ';'.join(sectors_affected)
    policy_issues = PolicyIssues(
        name=f'Policy Issues Integration Test {datetime.datetime.today()}',
        datahub_id=str(uuid.uuid4()),
        issue_type=issue_type,
        account_id=str(uuid.uuid4()),
        policy_areas=policy_areas,
        sentiment=sentiment,
        classification=classification,
        sectors_affected=sectors_effected,
        uk_region_affected=uk_region_name,
        event_id=str(uuid.uuid4()),  # Interaction id
    )
    policy_issues.description = faker.text()
    policy_issues.issue_rank = TopIssuesByRank.eight
    policy_issues.location_affected = ';'.join(country_names)
    policy_issues.uk_region_affected = uk_region_name
    return policy_issues


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
