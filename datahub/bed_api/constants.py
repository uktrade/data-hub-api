from collections import namedtuple
from enum import Enum

QueryConstant = namedtuple('QueryConstant', 'sql')


class ContactQuery(Enum):
    """Contact Query"""

    get_by_id = QueryConstant('SELECT Id, Email FROM Contact WHERE Id = {id}')


class Salutation(str, Enum):
    """Salutations from BED"""

    mr = 'Mr.'
    mrs = 'Mrs.'
    miss = 'Miss'
    # TODO: Others


class ContactType(str, Enum):
    """Contact Types from BED"""

    hmg_contact = 'HMG Contact'
    external = 'External Attendees'


class JobType(str, Enum):
    """Job Types from BED"""

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
    # TODO: Others


class BusinessArea(str, Enum):
    """Business Area Types from BED"""

    advanced_manufacturing = 'Advanced Manufacturing'
    professional = 'Professional & Business Services'
    civil_society = 'Civil Society'
    # TODO: Others
