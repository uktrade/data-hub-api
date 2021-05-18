from collections import namedtuple
from enum import Enum

QueryConstant = namedtuple('QueryConstant', ('sql', 'arg'))


class ContactQuery(Enum):
    """Contact Salesforce Queries"""

    get_by_id = QueryConstant(
        'SELECT Id '
        'FROM Contact '
        'WHERE Id = {id}',
        'id',
    )
    get_email_by_id = QueryConstant(
        'SELECT Id, Email '
        'FROM Contact '
        'WHERE Id = {id}',
        'id',
    )
    get_notes_by_id = QueryConstant(
        'SELECT Id, Notes__c '
        'FROM Contact '
        'WHERE Id = {id}',
        'id',
    )


class AccountQuery(Enum):
    """Account Salesforce Queries"""

    get_by_id = QueryConstant(
        'SELECT Id '
        'FROM Account '
        'WHERE Id = {id}',
        'id',
    )
    get_name_by_id = QueryConstant(
        'SELECT Id, Name '
        'FROM Account '
        'WHERE Id = {id}',
        'id',
    )


class EventQuery(Enum):
    """Event or Add Interaction Salesforce Queries"""

    get_by_id = QueryConstant(
        'SELECT Id '
        'FROM Event__c '
        'WHERE Id = {id}',
        'id',
    )

    count_event_by_date = QueryConstant(
        'SELECT COUNT(Id) '
        'FROM Event__c '
        'WHERE Date__c = {date}',
        'date',
    )

    get_event_id_by_date = QueryConstant(
        'SELECT Id FROM Event__c '
        'WHERE Date__c = {date} '
        'LIMIT {limit} OFFSET {offset}',
        'date,limit,offset',
    )


class EventAttendeeQuery(Enum):
    """Event Attendee Salesforce Queries"""

    get_by_id = QueryConstant(
        'SELECT Id '
        'FROM Event_Attendee__c '
        'WHERE Id = {id}',
        'id',
    )


class Salutation(str, Enum):
    """Salutations from BED"""

    none = ''
    not_applicable = 'N/A'
    mr = 'Mr.'
    mrs = 'Mrs.'
    miss = 'Miss'
    ms = 'Ms.'
    dr = 'Dr.'
    prof = 'Prof.'
    right_honourable = 'Rt Hon.'
    sir = 'Sir'
    lord = 'Lord'
    dame = 'Dame'


class ContactType(str, Enum):
    """Contact Types from BED"""

    none = ''
    hmg_contact = 'HMG Contact'
    external = 'External Attendees'


class JobType(str, Enum):
    """Job Types from BED"""

    none = ''
    ceo = 'CEO'
    chairperson = 'Chairperson'
    communications = 'Communications'
    consultant = 'Consultant'
    corporate_social_responsibility = 'Corporate Social Responsibility'
    director = 'Director'
    education = 'Education'
    engineering = 'Engineering'
    executive = 'Executive'
    finance = 'Finance'
    financial_director = 'Financial Director'
    founder = 'Founder'
    head_of_public_affairs = 'Head of Public Affairs'
    health_professional = 'Health Professional'
    hr = 'HR'
    legal = 'Legal'
    manager = 'Manager'
    operations = 'Operations'
    other = 'Other'
    owner = 'Owner'
    policy = 'Policy'
    president = 'President'
    public_affairs = 'Public Affairs'


class BusinessArea(str, Enum):
    """Business Area Types from BED"""

    none = ''
    advanced_manufacturing = 'Advanced Manufacturing'
    professional = 'Professional & Business Services'
    civil_society = 'Civil Society'
    consumer_and_retail = 'Consumer & Retail'
    creative_industries = 'Creative Industries'
    defense = 'Defence'
    education_and_research = 'Education & Research'
    energy = 'Energy'
    environmental_services = 'Environmental Services'
    financial_services = 'Financial Services'
    food_and_agriculture = 'Food & Agriculture'


class HighLevelSector(str, Enum):
    """High Level Sector Types from BED"""

    none = ''
    advanced_manufacturing = 'Advanced Manufacturing'
    civil_society = 'Civil Society'
    consumer_and_retail = 'Consumer & Retail'
    creative_industries = 'Creative Industries'
    defense = 'Defence'
    education_and_research = 'Education & Research'
    energy = 'Energy'
    environmental_services = 'Environmental Services'
    financial_services = 'Financial Services'
    food_and_agriculture = 'Food & Agriculture'


class LowLevelSector(str, Enum):
    """Low Level Sector Types from BED"""

    none = ''
    consumers = 'Consumers'
    retail = 'Retail'
    digital = 'Digital'
    digital_infrastructure = 'Digital Infrastructure'
    real_estate = 'Real Estate'
    telecoms = 'Telecoms'


class InteractionType(str, Enum):
    """Interaction Types from BED"""

    none = ''
    bilateral_meeting = 'Bilateral Meeting'
    brush_by = 'Brush By'
    conference = 'Conference'
    email = 'Email'
    forum = 'Forum'
    letter = 'Letter'
    multilateral_meeting = 'Multilateral Meeting'
    phone_call = 'Phone Call'
    reception = 'Reception'
    roadshow = 'Roadshow'


class TransparencyStatus(str, Enum):
    """Transparency Status from BED"""

    none = ''
    draft = 'Draft'
    confirm = 'Confirm'
    delete = 'Delete'


class IssueType(str, Enum):
    """Issue Types from BED"""

    none = ''
    covid_19 = 'Covid-19'
    domestic_policy = 'Domestic Policy'
    economic_opportunity = 'Economic Opportunity'
    economic_risk = 'Economic Risk'
    international_climate = 'International Climate'
    uk_transition_policy = 'UK Transition Policy'
    non_eu_trade_priority = 'Non-EU Trade Priority'


class DepartmentEyes(str, Enum):
    """Department Eyes from BED"""

    none = ''
    advanced_manufacturing = 'Advanced Manufacturing (BIS)'
    aviation = 'Aviation (DfT)'
    civil_society = 'Civil Society'
    consumer_and_retail = 'Consumer & Retail (BIS)'
    creative_industries = 'Creative Industries (DCMS)'
    defence = 'Defence (MoD)'
    energy = 'Energy (DECC)'
    environmental_services = 'Environmental Services'
    financial_services = 'Financial Services (HMT)'
    food_and_agriculture = 'Food & Agriculture (DEFRA)'


class SectorsAffected(str, Enum):
    """Sector(s) Affected from BED"""

    none = ''
    advanced_manufacturing = 'Advanced Manufacturing'
    consumer_and_retail = 'Consumer & Retail'
    creative_industries = 'Creative Industries'
    civil_society = 'Civil Society'
    defense = 'Defence'
    education_and_research = 'Education & Research'
    energy = 'Energy'
    environmental_services = 'Environmental Services'
    financial_services = 'Financial Services'
    food_and_agriculture = 'Food & Agriculture'
    health_and_social_care = 'Health and Social Care'
    infrastructure_construction_and_housing = 'Infrastructure, Construction & Housing'
    justice_rights_and_equality = 'Justice, Rights and Equality'
    life_sciences = 'Life Sciences'
    materials = 'Materials'
    media_and_broadcasting = 'Media & Broadcasting'
    pan_economy_trade_body = 'Pan-Economy Trade Body'
    professional_and_business_services = 'Professional & Business Services'
    tech_and_telecoms = 'Tech & Telecoms'
    tourism = 'Tourism'
    transport = 'Transport'

    class Sentiment(str, Enum):
        """Sentiment from BED"""

        none = ''
        positive = 'Positive'
        neutral = 'Neutral'
        negative = 'Negative'

    class Classification(str, Enum):
        """Classification from BED"""

        none = ''
        official_sensitive = 'Official-Sensitive'
        official = 'Official'
        unclassified = 'Unclassified'

    class TopIssuesByRank(str, Enum):
        """Top Issues by Rank from BED"""
        none = ''
        one = '1'
        two = '2'
        three = '3'
        four = '4'
        five = '5'
        six = '6'
        seven = '7'
        eight = '8'
        nine = '9'
        ten = '10'
