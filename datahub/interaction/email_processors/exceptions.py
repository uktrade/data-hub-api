class InvalidInviteError(Exception):
    """
    A custom exception for when the email invite is not valid.
    """


class MalformedEmailError(InvalidInviteError):
    """
    Exception for when the email was malformed in some way.
    """


class SenderUnverifiedError(InvalidInviteError):
    """
    Exception for when the sender could not be verified.
    """


class UnconfirmedCalendarInviteError(InvalidInviteError):
    """
    Exception for when the calendar invite was not confirmed.
    """


class BadCalendarInviteError(InvalidInviteError):
    """
    Exception for when the calendar invite was bad.
    """


class NoContactsError(InvalidInviteError):
    """
    Exception for when the email contains has no known Data Hub contacts as
    recipients.
    """
