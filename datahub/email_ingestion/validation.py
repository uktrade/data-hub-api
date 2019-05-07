from django.conf import settings


def _verify_authentication(message, from_email):
    # TODO: See if there's a library to make this a bit more bulletproof
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


def email_sent_by_dit(message):
    """
    Checks whether an email message was sent by a valid DIT address.

    :param message: mailparse.MailParser object - the message to check

    :returns: True if the email was sent by DIT, False otherwise.
    """
    from_email = message.from_[0][1]
    # TODO: See if valid domains are recorded elsewhere in the codebase
    # and use this to keep things DRY
    from_domain_is_dit = any([
        domain for domain in settings.DIT_EMAIL_DOMAINS
        if from_email.endswith(domain)
    ])
    if not from_domain_is_dit:
        return False
    authentication_pass = _verify_authentication(message, from_email)
    return authentication_pass
