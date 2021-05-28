from collections import namedtuple
from enum import Enum

QueryConstant = namedtuple('QueryConstant', ('sql', 'arg'))


class ContactQuery(Enum):
    """Contact Salesforce Queries"""

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
