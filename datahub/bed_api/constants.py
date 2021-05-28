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
