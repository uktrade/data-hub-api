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
        result = list(map(lambda x: x.value, self._member_map_.values()))
        result.remove('')
        return result


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


class InteractionType(StringEnum):
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


class TransparencyStatus(StringEnum):
    """Transparency Status from BED"""

    none = ''
    draft = 'Draft'
    confirm = 'Confirm'
    delete = 'Delete'


class IssueType(StringEnum):
    """Issue Types from BED"""

    none = ''
    covid_19 = 'Covid-19'
    domestic_policy = 'Domestic Policy'
    economic_opportunity = 'Economic Opportunity'
    economic_risk = 'Economic Risk'
    international_climate = 'International Climate'
    uk_transition_policy = 'UK Transition Policy'
    non_eu_trade_priority = 'Non-EU Trade Priority'


class DepartmentEyes(StringEnum):
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


class Sentiment(StringEnum):
    """Sentiment from BED"""

    none = ''
    positive = 'Positive'
    neutral = 'Neutral'
    negative = 'Negative'


class Classification(StringEnum):
    """Classification from BED"""

    none = ''
    official_sensitive = 'Official-Sensitive'
    official = 'Official'
    unclassified = 'Unclassified'


class TopIssuesByRank(StringEnum):
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


class PolicyArea(StringEnum):
    """Policy Area from BED"""

    none = ''
    access_to_finance = 'Access to Finance'
    access_to_public_funding = 'Access to Public Funding (inc. EU funding)'
    agriculture = 'Agriculture (Regulation/Support)'
    announcement_feedback = 'Announcement Feedback'
    art_culture_sport_and_leisure = 'Art, Culture, Sport and Leisure'
    business_regulation = 'Business Regulation'
    # This value needs to be exactly the same as what is in Salesforce
    company_law_and_company_reporting = 'Company Law and Company \u200bReporting'
    competition_law_and_policy = 'Competition \u200bLaw and Policy'
    consumer_rights = 'Consumer Rights'
    customs_union = 'Customs Union'
    cybersecurity = 'Cybersecurity'
    data_policy_and_regulation = 'Data Policy and Regulation'
    devolved_administration_northern_ireland = 'Devolved Administration - Northern Ireland'
    devolved_administration_scotland = 'Devolved Administration - Scotland'
    devolved_administration_wales = 'Devolved Administration - Wales'
    education_and_skills = 'Education and Skills (including students)'
    employment_law_and_labour_market_policy = 'Employment Law and Labour Market Policy'
    energy = 'Energy (exploration, production, distribution and use)'
    energy_market_regulation = 'Energy Market Regulation'
    environmental_climate_law_and_policy = 'Environmental/ Climate Law and Policy'
    european_lobbying_feedback = 'European Lobbying Feedback'
    exporting_and_export_support = 'Exporting and Export Support'
    facility_locations = 'Facility Locations (Legal HQ/Factory/etc)'
    gender_pay = 'Gender Pay'
    government_communications = 'Government Communications'
    government_procurement = 'Government Procurement'
    # CHECK: why this value is not retained
    # nhs = 'NHS'
    imports = 'Imports'
    inclusive_economy = 'Inclusive Economy'
    industrial_strategy = 'Industrial Strategy'
    intellectual_property = 'Intellectual Property'
    law_and_justice = 'Law and Justice'
    local_government = 'Local Government'
    local_growth = 'Local Growth'
    loss_of_investment_jobs = 'Loss of Investment / Jobs'
    market_access = 'Market Access'
    migration_and_immigration = 'Migration and Immigration'
    movement_of_goods = 'Movement of Goods'
    movement_of_people_temporary = (
        'Movement of People - '
        'Temporary (foreign travel and short term contracts)'
    )
    movement_of_services = 'Movement of Services'
    national_security = 'National Security'
    new_disruptive_technologies = 'New/ Disruptive Technologies'
    new_investment_jobs = 'New Investment/Jobs;'
    northern_powerhouse = 'Northern Powerhouse'
    nuclear = 'Nuclear'
    other = 'Other'
    prevention = 'Prevention'
    regional_devolution = 'Regional Devolution'
    regulatory_divergence_opportunities = 'Regulatory Divergence Opportunities'
    repeal_bill = 'Repeal Bill'
    returnships = 'Returnships'
    rules_of_origin = 'Rules of Origin'
    science_r_and_d_and_innovation = 'Science, R&D and Innovation'
    social_care = 'Social Care'
    standards = 'Standards'
    state_aid = 'State Aid'
    supply_chains_and_raw_materials = 'Supply Chains and Raw Materials'
    tariffs_and_trade_policy = 'Tariffs and Trade Policy'
    tax_and_revenue = 'Tax and Revenue'
    technology = 'Technology'
    trading_standards_and_product_regulations = 'Trading Standards and Product Regulations'
    transportation = 'Transportation (Freight and People)'
    workforce = 'Workforce'
    cop26_adaptation_and_resilience = (
        'COP26 Adaptation and Resilience '
        '(including CCRI and Climate Action 100+)'
    )
    cop26_clean_transport = 'COP26 Clean Transport (including EV100)'
    cop26_energy_transitions = 'COP26 Energy Transitions (including RE100 and EP100)'
    cop26_finance = 'COP26 Finance (including TCFD)'
    cop26_nature = 'COP26 Nature (including supply chains)'
    cop26_participation_at_glasgow = 'COP26 - Participation at Glasgow'


class RegionOrInternational(StringEnum):
    """UK Region or International Affected from BED"""

    none = ''
    international = 'International'
    uk_wide = 'UK Wide'
    england = 'England'
    northern_ireland = 'Northern Ireland'
    scotland = 'Scotland'
    wales = 'Wales'
    east_of_england = 'East of England'
    east_midlands = 'East Midlands'
    london = 'London'
    north_east = 'North East'
    north_west = 'North West'
    south_east = 'South East'
    south_west = 'South West'
    west_midlands = 'West Midlands'
    yorkshire_and_the_humber = 'Yorkshire and the Humber'
    guernsey = 'Guernsey'
    jersey = 'Jersey'
    isle_of_man = 'Isle of Man'
