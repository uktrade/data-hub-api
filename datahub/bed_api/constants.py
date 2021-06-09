from enum import Enum


class StringEnum(str, Enum):
    """
    Enumeration representing lookup and picklist types that cast
    to a string value
    """

    def values(self):
        """
        Output values as a list
        :return: Values as list
        """
        return [item.value for item in self._member_map_.values() if item.value != '']


class Salutation(StringEnum):
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


class ContactType(StringEnum):
    """Contact Types from BED"""

    none = ''
    hmg_contact = 'HMG Contact'
    external = 'External Attendees'


class JobType(StringEnum):
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


class BusinessArea(StringEnum):
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


class HighLevelSector(StringEnum):
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


class LowLevelSector(StringEnum):
    """Low Level Sector Types from BED"""

    none = ''
    consumers = 'Consumers'
    retail = 'Retail'
    digital = 'Digital'
    digital_infrastructure = 'Digital Infrastructure'
    real_estate = 'Real Estate'
    telecoms = 'Telecoms'


class SectorsAffected(StringEnum):
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
