from authres import AuthenticationResultsHeader
from django.conf import settings


def _verify_authentication(message, auth_methods=None):
    """
    Verify the Authentication-Results header of a MailParser object.

    :param message: mailparse.MailParser object - the message to check
    :param auth_methods: Optional - An iterable of email authentication methods
        to check.  Defaults to ('dkim', 'spf', 'dmarc').

    :returns: A boolean for whether or not the Authentication-Results header
        was verified.
    """
    if not auth_methods:
        auth_methods = ('dkim', 'spf', 'dmarc')
    header_contents = ' '.join(message.authentication_results.split('\n'))
    auth_parser = AuthenticationResultsHeader.parse(f'Authentication-Results: {header_contents}')
    auth_results = {auth_method: False for auth_method in auth_methods}
    for auth_mechanism in auth_parser.results:
        if auth_mechanism.method in auth_results.keys():
            auth_results[auth_mechanism.method] = auth_mechanism.result == 'pass'
    all_auth_pass = all(auth_results.values())
    return all_auth_pass


def was_email_sent_by_dit(message):
    """
    Checks whether an email message was sent by a valid DIT address.

    :param message: mailparse.MailParser object - the message to check

    :returns: True if the email was sent by DIT, False otherwise.
    """
    try:
        from_email = message.from_[0][1]
        from_domain = from_email.rsplit('@', maxsplit=1)[1]
    except IndexError:
        return False
    from_domain_is_dit = any([
        domain for domain in settings.DIT_EMAIL_DOMAINS
        if from_domain == domain
    ])
    if not from_domain_is_dit:
        return False
    from_domain_is_authentication_exempt = any([
        domain for domain in settings.DIT_EMAIL_DOMAINS_AUTHENTICATION_EXEMPT
        if from_domain == domain
    ])
    if from_domain_is_authentication_exempt:
        return True
    authentication_pass = _verify_authentication(message)
    return authentication_pass
