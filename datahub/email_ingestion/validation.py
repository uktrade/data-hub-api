from django.conf import settings


def _verify_authentication(message, from_email):
    authentication_lines = [
        line.strip() for line in message.authentication_results.split('\n')
    ]
    auth_results = {
        'dkim': False,
        'spf': False,
        'dmarc': False,
    }
    for line in authentication_lines:
        if line.startswith('dkim'):
            auth_results['dkim'] = line.startswith('dkim=pass')
        if line.startswith('spf'):
            spf_valid = (
                line.startswith('spf=pass') and line.endswith(f'smtp.mailfrom={from_email};')
            )
            auth_results['spf'] = spf_valid
        if line.startswith('dmarc'):
            auth_results['dmarc'] = line.startswith('dmarc=pass')
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
    authentication_pass = _verify_authentication(message, from_email)
    return authentication_pass
