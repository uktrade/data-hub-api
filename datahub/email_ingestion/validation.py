import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)


ALL_AUTH_METHODS = ('spf', 'dkim', 'dmarc', 'compauth')


def _get_auth_headers(message):
    """When message passes through multiple servers, the authentication_results becomes an array."""
    authentication_results = (
        message.authentication_results[0]
        if isinstance(
            message.authentication_results,
            list,
        )
        else message.authentication_results
    )

    return ' '.join(authentication_results.splitlines())


def _verify_authentication(message, auth_methods):
    """Verify the Authentication-Results header of a MailParser object.

    :param message: mailparse.MailParser object - the message to check
    :param auth_methods: An iterable of pairs of email authentication methods
        to and their minimum results to check.

    :returns: A boolean for whether or not the Authentication-Results header
        was verified.
    """
    header_contents = _get_auth_headers(message)
    auth_results = {auth_method: False for auth_method, _ in auth_methods}

    for auth_method, minimum_result in auth_methods:
        expected_auth_pairs = [f'{auth_method}={minimum_result}']
        if minimum_result == 'bestguesspass':
            expected_auth_pairs.append(f'{auth_method}=pass')

        expected_auth_pair_present = any(
            expected_auth_pair in header_contents for expected_auth_pair in expected_auth_pairs
        )

        if expected_auth_pair_present:
            auth_results[auth_method] = True

    all_auth_pass = all(auth_results.values())
    return all_auth_pass


def _log_unknown_domain(from_domain, message):
    log_auth_methods = r'|'.join(re.escape(auth_method) for auth_method in ALL_AUTH_METHODS)
    auth_header_contents = _get_auth_headers(message)
    authentication_results = re.findall(
        rf'((?:{log_auth_methods})=[a-z0-9]+)',
        auth_header_contents,
        flags=re.IGNORECASE,
    )
    logger.error(
        f'Domain "{from_domain}" not present in DIT_EMAIL_DOMAINS setting.',
        extra={'authentication_results': authentication_results},
    )


def was_email_sent_by_dit(message):
    """Checks whether an email message was sent by a valid DIT address.

    :param message: mailparse.MailParser object - the message to check

    :returns: True if the email passed our minimal level of email authentication checks.
    """
    try:
        from_email = message.from_[0][1].strip()
        from_domain = from_email.rsplit('@', maxsplit=1)[1]
    except IndexError:
        return False

    if from_email.lower() in settings.DIT_EMAIL_INGEST_BLOCKLIST:
        return False

    try:
        domain_auth_methods = settings.DIT_EMAIL_DOMAINS[from_domain]
    except KeyError:
        _log_unknown_domain(from_domain, message)
        return False

    from_domain_is_authentication_exempt = domain_auth_methods == [['exempt']]
    if from_domain_is_authentication_exempt:
        return True
    authentication_pass = _verify_authentication(message, domain_auth_methods)
    return authentication_pass
