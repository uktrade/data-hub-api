from django.conf import settings


def _verify_authentication(message, auth_methods=None):
    """
    Verify the Authentication-Results header of a MailParser object.

    :param message: mailparse.MailParser object - the message to check
    :param auth_methods: Optional - An iterable of pairs of email authentication methods
        to and their minimum results to check.
        Defaults to (('dkim', 'pass'), ('spf', 'pass'), ('dmarc', 'pass')).

    :returns: A boolean for whether or not the Authentication-Results header
        was verified.
    """
    if not auth_methods:
        auth_methods = (('dkim', 'pass'), ('spf', 'pass'), ('dmarc', 'pass'))
    header_contents = ' '.join(message.authentication_results.splitlines())
    auth_results = {auth_method: False for auth_method, _ in auth_methods}

    for auth_method, minimum_result in auth_methods:
        expected_auth_pairs = [f'{auth_method}={minimum_result}']
        if minimum_result == 'bestguesspass':
            expected_auth_pairs.append(f'{auth_method}=pass')

        expected_auth_pair_present = any(
            expected_auth_pair in header_contents
            for expected_auth_pair in expected_auth_pairs
        )

        if expected_auth_pair_present:
            auth_results[auth_method] = True

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

    try:
        domain_auth_methods = settings.DIT_EMAIL_DOMAINS[from_domain]
    except KeyError:
        # The domain is not in our known dictionary of DIT email domains
        return False

    from_domain_is_authentication_exempt = domain_auth_methods == ['exempt']
    if from_domain_is_authentication_exempt:
        return True
    authentication_pass = _verify_authentication(message, domain_auth_methods)
    return authentication_pass
