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


class EventQuery(Enum):
    """Event or Add Interaction Salesforce Queries"""

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
