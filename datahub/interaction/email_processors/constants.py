from enum import Enum


class InvalidInviteErrorCode(Enum):

    malformed_email = 'malformed_email'
    sender_unverified = 'sender_unverified'
    no_known_contacts = 'no_known_contacts'
    bad_calendar_format = 'bad_calendar_format'


USER_READABLE_ERROR_MESSAGES = {
    InvalidInviteErrorCode.no_known_contacts: (
        'The calendar invitation you sent to Data Hub did not include an email address '
        'that is recognised as a contact on Data Hub. The invitation must also be sent '
        'to Data Hub at the same time (and not forwarded to Data Hub later). Please '
        'check both of these things when resending your invitation and if you still '
        'see this message after resending the invitation, contact the Data Hub support '
        'team.',
    ),
    InvalidInviteErrorCode.bad_calendar_format: (
        'It looks like you sent something to Data Hub that was not a calendar invitation. '
        'Please send to Data Hub a calendar invitation (not an email or another type of '
        'message). If you still see this error message after sending a calendar email, '
        'please contact the Data Hub support team.',
    ),
}
