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
        try:
            if line.startswith('dkim'):
                assert line.startswith('dkim=pass')
                auth_results['dkim'] = True
            if line.startswith('spf'):
                assert line.startswith('spf=pass')
                assert line.endswith('smtp.mailfrom=%s;' % from_email)
                auth_results['spf'] = True
            if line.startswith('dmarc'):
                assert line.startswith('dmarc=pass')
                auth_results['dmarc'] = True
        except AssertionError:
            return False
    all_auth_pass = all(auth_results.values())
    if not all_auth_pass:
        return False
    return True


def email_sent_by_dit(message):
    """
    Checks whether an email message was sent by a valid DIT address.

    :param message: mailparse.MailParser object - the message to check

    :returns: True if the email was sent by DIT, False otherwise.
    """
    from_email = message.from_[0][1]
    # TODO: See if valid domains are recorded elsewhere in the codebase
    # and use this to keep things DRY
    dit_domains = ['@trade.gov.uk', '@digital.trade.gov.uk']
    from_domain_is_dit = any([
        domain for domain in dit_domains
        if from_email.endswith(domain)
    ])
    if not from_domain_is_dit:
        return False
    authentication_pass = _verify_authentication(message, from_email)
    return authentication_pass
