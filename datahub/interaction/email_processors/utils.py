from datahub.company.models import Advisor


def get_best_match_adviser_by_email(email):
    """
    Get the best-guess matching active adviser for a particular correspondence email
    address.

    This firstly attempts to get the oldest Advisor object with a (case insensitive) matching
    `contact_email`, it will then attempt to match on (case insensitive) `email`.  We prefer
    `contact_email` over `email` as this should most closely match the correspondence
    email address - the context here is that we are dealing with the email
    accounts that advisers use for setting up meetings/emailing companies.

    :param email: string email address
    :returns: an Advisor object or None, if a match could not be found
    """
    for field in ['contact_email', 'email']:
        criteria = {f'{field}__iexact': email, 'is_active': True}
        try:
            return Advisor.objects.filter(**criteria).earliest('date_joined')
        except Advisor.DoesNotExist:
            continue
    return None


def get_all_recipients(message):
    """
    Get all of the recipient emails from a MailParser message object.

    :returns: a set of all recipient emails
    """
    return {email.strip() for name, email in (*message.to, *message.cc)}
