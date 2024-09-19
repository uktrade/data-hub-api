import logging

from datahub.company.models.company import Company

logger = logging.getLogger(__name__)


def match_by_duns_number(duns_number):
    """Uses an EYB lead provided DnB number
    to search Data Hub for existing Companies

    Args:
        duns_number (string): a DnB number
    Returns:
        found (boolean): true/false based on success of search
        company (object): a Company object or None
    """
    companies = Company.objects.filter(duns_number=duns_number)

    if companies.count() == 1:
        return True, companies[0]

    # no match found
    return False, None


def process_eyb_lead(eyb_lead):
    """Matches an EYB lead with an existing Company via DnB number

    Args:
        eyb_lead (object): an EYB lead object
    """
    if eyb_lead.duns_number is not None:
        found, company = match_by_duns_number(eyb_lead.duns_number)

        if found:
            eyb_lead.company = company
            eyb_lead.save()
