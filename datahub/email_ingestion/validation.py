def email_sent_by_dit(message):
    """
    """
    from_email = message.from_[0][1]
    # TODO: See if valid domains are recorded elsewhere in the codebase
    # and use this to keep things DRY
    dit_domains = ["@trade.gov.uk", "@digital.trade.gov.uk"]
    from_domain_is_dit = any([
        domain for domain in dit_domains
        if from_email.endswith(domain)
    ])
    if not from_domain_is_dit:
        return False
    authentication_lines = [
        line.strip() for line in message.authentication_results.split('\n')
    ]
    # TODO: See if there's a library to make this a bit more bulletproof
    for line in authentication_lines:
        try:
            if line.startswith("dkim"):
                assert(line.startswith("dkim=pass"))
            if line.startswith("spf"):
                assert(line.startswith("spf=pass"))
                assert(line.endswith("smtp.mailfrom=%s;" % from_email))
            if line.startswith("dmarc"):
                assert(line.startswith("dmarc=pass"))
        except AssertionError:
            return False
    return True
