import logging

from django.db.models import Q, F

from datahub.company.models.company import Company
from datahub.company.models.contact import Contact
from datahub.investment_lead.models import EYBLead

logger = logging.getLogger(__name__)


def link_leads_to_companies():
    queryset = EYBLead.objects.filter(archived=False).filter(
        Q(user_hashed_uuid=F('triage_hashed_uuid')),
        company__isnull=True,
    )

    # match_or_create_company_for_eyb_lead
    # then
    # create_or_skip_eyb_lead_as_company_contact


def raise_exception_for_eyb_lead_without_company(eyb_lead: EYBLead):
    """
    Check for required attributes on EYB Lead to ensure there is a company
    """
    if not eyb_lead.company:
        raise AttributeError('The ''company'' attribute is not set for the ''EYBLead'' object.')


def find_match_by_duns_number(duns_number):
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
        return companies[0]

    # no match found
    return None


def add_new_company_from_eyb_lead(eyb_lead: EYBLead):
    """
    Add new company from EYB lead and link it.
    """
    # Create company record
    company = Company()
    company.duns_number = eyb_lead.duns_number
    company.name = eyb_lead.company_name
    company.sector = eyb_lead.sector
    company.address_1 = eyb_lead.address_1
    company.address_2 = eyb_lead.address_2
    company.address_town = eyb_lead.address_town
    company.address_county = eyb_lead.address_county
    if eyb_lead.address_country is None:
        raise ValueError('Address country field is required to create a new company')
    else:
        company.address_country = eyb_lead.address_country
    company.address_postcode = eyb_lead.address_postcode
    company.website = eyb_lead.company_website

    company.save()

    return company


def match_or_create_company_for_eyb_lead(eyb_lead):
    """Matches an EYB lead with an existing Company via DnB number

    Args:
        eyb_lead (object): an EYB lead object
    Returns:
        company (object): a company object
    """
    company = None
    if eyb_lead.duns_number is not None:
        company = find_match_by_duns_number(eyb_lead.duns_number)

    if company is None:
        company = add_new_company_from_eyb_lead(eyb_lead)

    eyb_lead.company = company
    eyb_lead.save()
    return company


def email_matches_contact_on_eyb_lead_company(eyb_lead: EYBLead):
    """
    Check whether a contact exists with the EYB lead email address on the EYB Lead company
    """
    raise_exception_for_eyb_lead_without_company(eyb_lead)

    count = Contact.objects.filter(
        company=eyb_lead.company,
        email__iexact=eyb_lead.email,  # iexact; case-insensitive exact match
    ).count()
    return count >= 1


def create_company_contact_for_eyb_lead(eyb_lead: EYBLead):
    """
    Given an EYB lead with a linked company record:
    Create a company contact
    """
    raise_exception_for_eyb_lead_without_company(eyb_lead)

    contact = Contact()
    contact.company = eyb_lead.company
    contact.email = eyb_lead.email
    contact.full_telephone_number = eyb_lead.telephone_number
    contact.job_title = eyb_lead.role
    contact.first_name = eyb_lead.full_name
    contact.last_name = eyb_lead.full_name
    contact.address_same_as_company = True
    contact.primary = True

    contact.save()

    return contact


def create_or_skip_eyb_lead_as_company_contact(eyb_lead: EYBLead):
    """
    Given an EYB Lead with a linked company record:
    Create new company contact if not exists
    """
    raise_exception_for_eyb_lead_without_company(eyb_lead)

    if not email_matches_contact_on_eyb_lead_company(eyb_lead):
        create_company_contact_for_eyb_lead(eyb_lead)
