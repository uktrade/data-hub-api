import logging

from datahub.company.models.company import Company

logger = logging.getLogger(__name__)


def match_by_duns_number(duns_number):
    """ Uses an EYB lead provided DnB number
    to search Data Hub for existing Companies

    Args:
        duns_number (string): a DnB number
    """
    companies = Company.objects.filter(duns_number=duns_number)

    if len(companies) == 1:
        # match found
        return True, companies[0]

    # TODO: what to do if len > 1?
    return False, None


def process_eyb_lead(eyb_lead):
    """_summary_

    Args:
        eyb_lead (_type_): _description_
    """
    return
