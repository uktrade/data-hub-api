# Is this file needed?? - get_by_id queries can just be put directly into the base_repository
# None of the other queries appear to be used yet

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


class PolicyIssuesQuery(Enum):
    """Policy Issues Salesforce Queries"""

    get_by_id = QueryConstant(
        'SELECT Id '
        'FROM Policy_Issues__c '
        'WHERE Id = {id}',
        'id',
    )


class EventAttendeeQuery(Enum):
    """Event Attendee Salesforce Queries"""

    get_by_id = QueryConstant(
        'SELECT Id '
        'FROM Event_Attendee__c '
        'WHERE Id = {id}',
        'id',
    )
